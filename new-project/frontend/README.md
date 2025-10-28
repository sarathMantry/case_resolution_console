# Frontend Application

This directory contains the frontend application of the project.

## Setup Instructions

1. **Install Dependencies**: 
   Run the following command to install the necessary dependencies:
   ```
   npm install
   ```

2. **Build the Docker Image**: 
   Use the following command to build the Docker image:
   ```
   docker build -t frontend .
   ```

3. **Run the Application**: 
   To run the application, use:
   ```
   docker-compose up
   ```

## Usage

After running the application, you can access it at `http://localhost:3000` (or the port specified in your `docker-compose.yml`).

## Project Structure

- `src/`: Contains the source files for the frontend application.
- `index.html`: The main HTML file.
- `main.js`: The JavaScript file containing the application logic.

## Contributing

Feel free to submit issues or pull requests for improvements or bug fixes.