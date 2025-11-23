const express = require('express');
const cors = require('cors');
const { Pool } = require('pg');
const amqp = require('amqplib');
require('dotenv').config();

const app = express();
app.use(cors());
app.use(express.json());

// PostgreSQL connection
const pool = new Pool({
    host: process.env.DB_HOST || 'database',
    port: process.env.DB_PORT || 5432,
    database: process.env.DB_NAME || 'nutrimarket',
    user: process.env.DB_USER || 'postgres',
    password: process.env.DB_PASSWORD || 'postgres',
});

// RabbitMQ connection
let channel = null;
const QUEUE_NAME = 'ml_predictions';

async function connectRabbitMQ() {
    try {
        const connection = await amqp.connect(
            `amqp://${process.env.RABBITMQ_USER || 'guest'}:${process.env.RABBITMQ_PASSWORD || 'guest'}@${process.env.RABBITMQ_HOST || 'rabbitmq'}:5672`
        );
        channel = await connection.createChannel();
        await channel.assertQueue(QUEUE_NAME, { durable: true });
        console.log('✅ Connected to RabbitMQ');

        // Start consuming messages
        consumePredictions();
    } catch (error) {
        console.error('❌ RabbitMQ connection failed:', error.message);
        setTimeout(connectRabbitMQ, 5000); // Retry after 5s
    }
}

// Health check
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'ml-service-api' });
});

// Get ML models
app.get('/api/models', async (req, res) => {
    try {
        const result = await pool.query(
            'SELECT * FROM ml_models WHERE is_active = true ORDER BY created_at DESC'
        );
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get user balance
app.get('/api/balance/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const result = await pool.query(
            'SELECT balance FROM profiles WHERE id = $1',
            [userId]
        );

        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'User not found' });
        }

        res.json({ balance: parseFloat(result.rows[0].balance) });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Top-up balance
app.post('/api/balance/topup', async (req, res) => {
    try {
        const { userId, amount } = req.body;

        const result = await pool.query(
            'SELECT create_top_up_transaction($1, $2) as transaction_id',
            [userId, amount]
        );

        res.json({
            success: true,
            transaction_id: result.rows[0].transaction_id
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Create prediction (send to RabbitMQ queue)
app.post('/api/predictions', async (req, res) => {
    try {
        const { userId, modelId, inputData } = req.body;

        // Get model cost
        const modelResult = await pool.query(
            'SELECT cost_per_prediction FROM ml_models WHERE id = $1',
            [modelId]
        );

        if (modelResult.rows.length === 0) {
            return res.status(404).json({ error: 'Model not found' });
        }

        const cost = parseFloat(modelResult.rows[0].cost_per_prediction);

        // Check balance
        const balanceResult = await pool.query(
            'SELECT balance FROM profiles WHERE id = $1',
            [userId]
        );

        const balance = parseFloat(balanceResult.rows[0].balance);

        if (balance < cost) {
            return res.status(400).json({
                error: 'Insufficient balance',
                balance,
                required: cost
            });
        }

        // Create prediction
        const predictionResult = await pool.query(
            `INSERT INTO predictions (user_id, model_id, input_data, cost, status) 
       VALUES ($1, $2, $3, $4, 'pending') 
       RETURNING id`,
            [userId, modelId, inputData, cost]
        );

        const predictionId = predictionResult.rows[0].id;

        // Deduct balance
        await pool.query(
            'SELECT create_deduction_transaction($1, $2, $3, $4)',
            [userId, cost, predictionId, 'ML Prediction']
        );

        // Send to RabbitMQ for processing
        if (channel) {
            channel.sendToQueue(
                QUEUE_NAME,
                Buffer.from(JSON.stringify({ predictionId })),
                { persistent: true }
            );
        }

        res.json({
            success: true,
            prediction_id: predictionId,
            status: 'queued'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get predictions
app.get('/api/predictions/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const { status } = req.query;

        let query = 'SELECT * FROM predictions WHERE user_id = $1';
        const params = [userId];

        if (status) {
            query += ' AND status = $2';
            params.push(status);
        }

        query += ' ORDER BY created_at DESC LIMIT 50';

        const result = await pool.query(query, params);
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Get transactions
app.get('/api/transactions/:userId', async (req, res) => {
    try {
        const { userId } = req.params;
        const result = await pool.query(
            'SELECT * FROM transactions WHERE user_id = $1 ORDER BY created_at DESC LIMIT 100',
            [userId]
        );
        res.json(result.rows);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Process predictions from RabbitMQ queue
async function consumePredictions() {
    if (!channel) return;

    channel.consume(QUEUE_NAME, async (msg) => {
        if (!msg) return;

        try {
            const { predictionId } = JSON.parse(msg.content.toString());
            console.log(`📊 Processing prediction: ${predictionId}`);

            // Get prediction details
            const result = await pool.query(
                'SELECT p.*, m.model_type FROM predictions p JOIN ml_models m ON p.model_id = m.id WHERE p.id = $1',
                [predictionId]
            );

            if (result.rows.length === 0) {
                throw new Error('Prediction not found');
            }

            const prediction = result.rows[0];

            // Update status to processing
            await pool.query(
                "UPDATE predictions SET status = 'processing', started_at = NOW() WHERE id = $1",
                [predictionId]
            );

            // Call Hugging Face API
            const startTime = Date.now();
            const mlResult = await callHuggingFace(prediction.model_type, prediction.input_data);
            const processingTime = Date.now() - startTime;

            // Update with result
            await pool.query(
                `UPDATE predictions 
         SET status = 'completed', output_data = $1, completed_at = NOW(), processing_time_ms = $2
         WHERE id = $3`,
                [mlResult, processingTime, predictionId]
            );

            console.log(`✅ Prediction completed: ${predictionId}`);
            channel.ack(msg);

        } catch (error) {
            console.error(`❌ Prediction failed:`, error.message);

            // Mark as failed
            const { predictionId } = JSON.parse(msg.content.toString());
            await pool.query(
                "UPDATE predictions SET status = 'failed', error_message = $1, completed_at = NOW() WHERE id = $2",
                [error.message, predictionId]
            );

            channel.ack(msg);
        }
    }, { noAck: false });
}

// Call Hugging Face API
async function callHuggingFace(modelType, inputData) {
    const HF_API_KEY = process.env.HUGGINGFACE_API_KEY;

    if (!HF_API_KEY) {
        return { error: 'HuggingFace API key not configured' };
    }

    let prompt = '';

    if (modelType === 'regression') {
        prompt = `Analyze ingredients: ${inputData.ingredients.join(', ')}. 
    Return JSON only: {"calories_per_serving": <number>, "protein_g": <number>, "carbs_g": <number>, "fat_g": <number>}`;
    } else if (modelType === 'recommendation') {
        prompt = `Suggest 3 substitutes for "${inputData.ingredient}". Return JSON array only.`;
    } else {
        prompt = `Generate meal plan. Return JSON only.`;
    }

    try {
        const response = await fetch(
            'https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2',
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${HF_API_KEY}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    inputs: prompt,
                    parameters: {
                        max_new_tokens: 300,
                        temperature: 0.5
                    }
                })
            }
        );

        if (!response.ok) {
            throw new Error(`HuggingFace API error: ${response.status}`);
        }

        const result = await response.json();
        const text = result[0]?.generated_text || '';

        // Try to parse JSON from response
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        }

        return { result: text.substring(0, 200) };

    } catch (error) {
        console.error('HuggingFace error:', error);
        return { error: error.message, fallback: 'Could not generate prediction' };
    }
}

// Initialize
const PORT = process.env.PORT || 3001;

async function start() {
    try {
        // Test DB connection
        await pool.query('SELECT NOW()');
        console.log('✅ Connected to PostgreSQL');

        // Connect to RabbitMQ
        await connectRabbitMQ();

        app.listen(PORT, () => {
            console.log(`🚀 ML Service API running on port ${PORT}`);
        });
    } catch (error) {
        console.error('❌ Startup failed:', error);
        process.exit(1);
    }
}

start();
