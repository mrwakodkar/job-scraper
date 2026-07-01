#!/usr/bin/env python3
"""
Netherlands Job Search — Playwright-based Scraper
Fast, lightweight, async support
Runs daily via GitHub Actions at 2 PM IST (8:30 AM UTC)

Author: Minar Mehar
Created: 2026-06-30
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, Page

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════════
# SCRAPER FUNCTIONS (Async with Playwright)
# ════════════════════════════════════════════════════════════════════════════════

async def scrape_indeed_nl(page: Page) -> List[Dict]:
    """Scrape Indeed.nl"""
    logger.info("Scraping Indeed.nl...")
    jobs = []
    try:
        url = "https://nl.indeed.com/jobs?q=risk+analyst&l=Netherlands&start=0"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('[data-testid="job-card-container"]', timeout=15000)
        await page.wait_for_timeout(2000)  # Wait for dynamic content

        # Get all job cards
        job_cards = await page.query_selector_all('[data-testid="job-card-container"]')
        logger.info(f"Found {len(job_cards)} job containers on Indeed")

        for job_card in job_cards[:20]:
            try:
                # Extract job details
                title_elem = await job_card.query_selector('h2.jobTitle span')
                company_elem = await job_card.query_selector('span.companyName')

                title = await title_elem.text_content() if title_elem else None
                company = await company_elem.text_content() if company_elem else None

                if not title or not company:
                    continue

                # Try to get salary
                salary_elem = await job_card.query_selector('div.salary-snippet')
                salary = await salary_elem.text_content() if salary_elem else "Not listed"

                # Get job URL
                link_elem = await job_card.query_selector('a[data-jk]')
                job_id = await link_elem.get_attribute('data-jk') if link_elem else None
                job_url = f"https://nl.indeed.com/viewjob?jk={job_id}" if job_id else ""

                if title and company and job_url:
                    jobs.append({
                        'title': title.strip(),
                        'company': company.strip(),
                        'location': "Netherlands",
                        'salary': salary.strip(),
                        'url': job_url,
                        'source': 'Indeed.nl',
                        'timestamp': datetime.now().isoformat()
                    })
            except Exception as e:
                logger.debug(f"Error parsing Indeed job: {str(e)}")
                continue

        logger.info(f"Indeed.nl: Found {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Indeed.nl scraping error: {str(e)}")

    return jobs

async def scrape_iamexpat_nl(page: Page) -> List[Dict]:
    """Scrape IamExpat.nl (visa-sponsorship focused)"""
    logger.info("Scraping IamExpat.nl...")
    jobs = []
    try:
        url = "https://www.iamexpat.nl/jobs?search=risk&country=Netherlands"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('div.job-result', timeout=15000)
        await page.wait_for_timeout(2000)

        job_results = await page.query_selector_all('div.job-result')
        logger.info(f"Found {len(job_results)} job containers on IamExpat")

        for job in job_results[:20]:
            try:
                title_elem = await job.query_selector('h3')
                title = await title_elem.text_content() if title_elem else None

                if not title:
                    continue

                # Get company
                company_elem = await job.query_selector('span.company-name')
                company = await company_elem.text_content() if company_elem else "Unknown"

                # Get salary
                salary_elem = await job.query_selector('span.salary')
                salary = await salary_elem.text_content() if salary_elem else "Not listed"

                # Get URL
                link_elem = await job.query_selector('a')
                job_url = await link_elem.get_attribute('href') if link_elem else None

                if not job_url:
                    continue

                if not job_url.startswith('http'):
                    job_url = f"https://www.iamexpat.nl{job_url}"

                jobs.append({
                    'title': title.strip(),
                    'company': company.strip(),
                    'location': "Netherlands",
                    'salary': salary.strip(),
                    'url': job_url,
                    'source': 'IamExpat.nl',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.debug(f"Error parsing IamExpat job: {str(e)}")
                continue

        logger.info(f"IamExpat.nl: Found {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"IamExpat.nl scraping error: {str(e)}")

    return jobs

async def scrape_undutchables(page: Page) -> List[Dict]:
    """Scrape Undutchables (internationals-focused)"""
    logger.info("Scraping Undutchables...")
    jobs = []
    try:
        url = "https://www.undutchables.com/jobs?q=risk&country=Netherlands"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('div.job-result', timeout=15000)
        await page.wait_for_timeout(2000)

        job_results = await page.query_selector_all('div.job-result')
        logger.info(f"Found {len(job_results)} job containers on Undutchables")

        for job in job_results[:20]:
            try:
                title_elem = await job.query_selector('h2')
                title = await title_elem.text_content() if title_elem else None

                if not title:
                    continue

                company_elem = await job.query_selector('span.company')
                company = await company_elem.text_content() if company_elem else "Unknown"

                salary_elem = await job.query_selector('span.salary')
                salary = await salary_elem.text_content() if salary_elem else "Not listed"

                link_elem = await job.query_selector('a')
                job_url = await link_elem.get_attribute('href') if link_elem else None

                if not job_url:
                    continue

                if not job_url.startswith('http'):
                    job_url = f"https://www.undutchables.com{job_url}"

                jobs.append({
                    'title': title.strip(),
                    'company': company.strip(),
                    'location': "Netherlands",
                    'salary': salary.strip(),
                    'url': job_url,
                    'source': 'Undutchables',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.debug(f"Error parsing Undutchables job: {str(e)}")
                continue

        logger.info(f"Undutchables: Found {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Undutchables scraping error: {str(e)}")

    return jobs

async def scrape_monsterboard_nl(page: Page) -> List[Dict]:
    """Scrape Monsterboard.nl"""
    logger.info("Scraping Monsterboard.nl...")
    jobs = []
    try:
        url = "https://www.monsterboard.nl/en/jobs/risk-analyst/in-netherlands"
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('div.job-listing', timeout=15000)
        await page.wait_for_timeout(2000)

        job_listings = await page.query_selector_all('div.job-listing')
        logger.info(f"Found {len(job_listings)} job containers on Monsterboard")

        for job in job_listings[:20]:
            try:
                title_elem = await job.query_selector('h2')
                title = await title_elem.text_content() if title_elem else None

                if not title:
                    continue

                company_elem = await job.query_selector('span.company')
                company = await company_elem.text_content() if company_elem else "Unknown"

                salary_elem = await job.query_selector('span.salary')
                salary = await salary_elem.text_content() if salary_elem else "Not listed"

                link_elem = await job.query_selector('a')
                job_url = await link_elem.get_attribute('href') if link_elem else None

                if not job_url:
                    continue

                jobs.append({
                    'title': title.strip(),
                    'company': company.strip(),
                    'location': "Netherlands",
                    'salary': salary.strip(),
                    'url': job_url,
                    'source': 'Monsterboard.nl',
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.debug(f"Error parsing Monsterboard job: {str(e)}")
                continue

        logger.info(f"Monsterboard.nl: Found {len(jobs)} jobs")
    except Exception as e:
        logger.error(f"Monsterboard.nl scraping error: {str(e)}")

    return jobs

# ════════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION (Async)
# ════════════════════════════════════════════════════════════════════════════════

async def run_all_scrapers() -> List[Dict]:
    """Run all scrapers concurrently with Playwright"""
    logger.info("=" * 80)
    logger.info(f"Job Search Scraper Started: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    all_jobs = []

    async with async_playwright() as p:
        # Launch browser (headless mode for GitHub Actions)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(30000)
        page.set_default_navigation_timeout(30000)

        try:
            # Define scrapers
            scrapers = [
                ("Indeed.nl", lambda: scrape_indeed_nl(page)),
                ("IamExpat.nl", lambda: scrape_iamexpat_nl(page)),
                ("Undutchables", lambda: scrape_undutchables(page)),
                ("Monsterboard.nl", lambda: scrape_monsterboard_nl(page)),
            ]

            # Run scrapers sequentially (can be concurrent if needed)
            for name, scraper_func in scrapers:
                try:
                    jobs = await scraper_func()
                    all_jobs.extend(jobs)
                    await page.wait_for_timeout(2000)  # 2 second delay between requests
                except Exception as e:
                    logger.error(f"Error running {name}: {str(e)}")
                    continue

            logger.info(f"Total jobs found: {len(all_jobs)}")

            # Deduplication
            unique_jobs = {}
            for job in all_jobs:
                url = job.get('url', '')
                if url and url not in unique_jobs:
                    unique_jobs[url] = job

            all_jobs = list(unique_jobs.values())
            logger.info(f"After deduplication: {len(all_jobs)} unique jobs")

            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"jobs_scraped_{timestamp}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_jobs, f, indent=2, ensure_ascii=False)

            logger.info(f"Results saved to: {output_file}")
            logger.info("=" * 80)

        finally:
            await context.close()
            await browser.close()

    return all_jobs

if __name__ == '__main__':
    # Run async main function
    jobs = asyncio.run(run_all_scrapers())
    print(f"\n✓ Scraped {len(jobs)} jobs from 4 portals")
    print(f"  Output: jobs_scraped_*.json")
