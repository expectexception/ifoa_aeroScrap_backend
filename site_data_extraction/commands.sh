#!/bin/bash
# Quick Reference Commands for Job Scraping System

echo "════════════════════════════════════════════════════════════════"
echo "🚀 JOB SCRAPING SYSTEM - QUICK REFERENCE"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📋 SCRAPING COMMANDS:"
echo "  python3 run_all_scrapers.py all                    # Run all scrapers"
echo "  python3 run_all_scrapers.py aviationjobsearch      # Run specific scraper"
echo "  python3 run_all_scrapers.py stats                  # View database stats"
echo ""

echo "📊 VIEW FILTERED RESULTS:"
echo "  python3 view_categories.py                         # Show all views"
echo "  python3 view_categories.py stats                   # Show statistics only"
echo "  python3 view_categories.py category                # Show by category"
echo "  python3 view_categories.py source                  # Show by source"
echo "  python3 view_categories.py search <keyword>        # Search jobs"
echo ""

echo "🔍 SEARCH EXAMPLES:"
echo "  python3 view_categories.py search operations       # Find operations jobs"
echo "  python3 view_categories.py search manager          # Find manager jobs"
echo "  python3 view_categories.py search dispatcher       # Find dispatcher jobs"
echo "  python3 view_categories.py search OCC              # Find OCC jobs"
echo ""

echo "🧪 TEST FILTER:"
echo "  python3 filter_manager.py                          # Test filter with samples"
echo ""

echo "📁 OUTPUT FILES:"
echo "  job_output.json                                    # Main output (all jobs)"
echo "  output/aviation_job_search_jobs_*.json            # Per-scraper results"
echo "  jobs.db                                            # SQLite database"
echo ""

echo "⚙️  CONFIGURATION:"
echo "  config.py                                          # Main config (limits, filter)"
echo "  filter_title.json                                  # Filter keywords"
echo "  filter_manager.py                                  # Filter logic"
echo ""

echo "📖 DOCUMENTATION:"
echo "  FILTER_GUIDE.md                                    # Complete filter guide"
echo "  README.md                                          # Project overview"
echo ""

echo "════════════════════════════════════════════════════════════════"
