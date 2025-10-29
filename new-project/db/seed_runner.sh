#!/bin/bash
# Script to wait for database and then seed KPI data

echo "⏳ Waiting for database to be ready..."
sleep 5

echo "🚀 Starting KPI data seeding..."
python /seed/seed_kpi_data.py

echo "✅ Seeding completed!"
