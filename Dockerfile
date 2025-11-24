FROM node:20-alpine

WORKDIR /app

# Копирование package files
COPY package*.json ./

# Установка зависимостей
RUN npm install

# Копирование исходного кода
COPY . .

# Открытие порта
EXPOSE 3000

# Запуск приложения
CMD ["npm", "run", "dev"]
