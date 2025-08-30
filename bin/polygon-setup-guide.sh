#!/bin/bash

echo "🔍 AI Stock Dashboard - Polygon API Setup Guide"
echo "================================================"
echo ""

echo "📋 The errors you're seeing are due to:"
echo "1. Rate limiting on Polygon.io free tier (5 calls/minute, 1000/day)"
echo "2. Invalid data format handling in the previous version"
echo ""

echo "✅ Fixes implemented:"
echo "- Added intelligent rate limiting with exponential backoff"
echo "- Improved error handling for different Polygon API response formats"
echo "- Added retry logic for transient failures"
echo "- Better parsing of Polygon API responses"
echo ""

echo "🔧 To set up Polygon API:"
echo "1. Get a free API key from: https://polygon.io/"
echo "2. Add it to your .env file:"
echo "   POLYGON_API_KEY=your_api_key_here"
echo ""

echo "📊 Current data source options:"
echo "- yahoo: Yahoo Finance (default, no API key needed)"
echo "- polygon: Polygon.io (requires API key, 5 calls/min free)"
echo "- alpha_vantage: Alpha Vantage (requires API key, 5 calls/min free)"
echo ""

echo "🚀 To switch to Polygon API:"
echo "1. Set your API key in .env"
echo "2. Update config via admin panel or directly in admin_config.json:"
echo '   {"data_source": "polygon"}'
echo ""

echo "⚠️  Rate Limiting Information:"
echo "- Polygon Free: 5 calls/minute, 1000/day"
echo "- The app now automatically handles rate limits"
echo "- Calls are spaced 12+ seconds apart"
echo "- Failed calls trigger exponential backoff"
echo ""

echo "🔄 To restart with the fixes:"
echo "docker-compose -f docker-compose.prod.yml restart"
echo ""

echo "📝 The app will now:"
echo "- Gracefully handle rate limits"
echo "- Show clear error messages"
echo "- Fall back to mock data in debug mode"
echo "- Retry failed requests intelligently"
