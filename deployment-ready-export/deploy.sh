#!/bin/bash

echo "Deploying GoatMeasure Pro..."

# Install dependencies
npm install

# Create uploads directory
mkdir -p uploads

# Build the application
npm run build

# Run database migrations
npm run db:push

echo "Build complete! Run 'npm start' to start the server."
