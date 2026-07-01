#!/usr/bin/env python3
"""
Netherlands Job Search — Playwright Scraper v2 (Resilient)
Improved timeouts, better error handling, retry logic
Runs daily via GitHub Actions at 2 PM IST (8:30 AM UTC)

Author: Minar Mehar
Created: 2026-07-01
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════════
# RESILIENT SCRAPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

async def scrape_indeed_nl(page: Page, retries: int = 2) -> List[Dict]:
    """Scrape Indeed.nl with retries and longer timeouts"""
    logger.info("Scraping Indeed.nl...")
    jobs = []

    for attempt in range(retries):
        try:
            url = "https://nl.indeed.com/jobs?q=risk+analyst&l=Netherlands&start=0"

            # Load page faster: use domcontentloaded instead of networkidle
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)  # Wait for JS rendering

            # Try to find job cards with generous timeout
            try:
                await page.wait_for_selector('[data-testid="job-card-container"]', timeout=20000)
            except PlaywrightTimeoutError:
                logger.warning("Indeed job cards not found, trying alternative selector...")
                # Fallback selector
                await page.wait_for_selector('div[class*="job"]', timeout=10000)

            # Extract jobs via JavaScript (more reliable)
            job_cards = await page.query_selector_all('[data-testid="job-card-container"]')

            if not job_cards:
                # Fallback: try alternative selectors
                job_cards = await page.query_selector_all('div.jobCard')

            logger.info(f"Found {len(job_cards)} job containers on Indeed")

            for i, job_card in enumerate(job_cards[:25]):
                try:
                    # Extract via JavaScript for reliability
                    job_data = await job_card.evaluate("""
                        (el) => {
                            const title = el.querySelector('h2')?.textContent?.trim() || 'N/A';
                            const company = el.querySelector('[data-testid="company-name"]')?.textContent?.trim() || 'N/A';
                            const salary = el.querySelector('.salary-snippet')?.textContent?.trim() || 'Not listed';
                            const link = el.querySelector('a[data-jk]');
                            const jobId = link?.getAttribute('data-jk') || '';
                            return { title, company, salary, jobId };
                        }
                    """)

                    if job_data['title'] != 'N/A' and job_data['jobId']:
                        jobs.append({
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'location': "Netherlands",
                            'salary': job_data['salary'],
                            'url': f"https://nl.indeed.com/viewjob?jk={job_data['jobId']}",
                            'source': 'Indeed.nl',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error extracting Indeed job {i}: {str(e)}")
                    continue

            logger.info(f"Indeed.nl: Found {len(jobs)} jobs (attempt {attempt + 1})")
            if jobs:
                return jobs  # Success, return early

        except PlaywrightTimeoutError as e:
            logger.warning(f"Indeed.nl timeout on attempt {attempt + 1}/{retries}: {str(e)}")
            await page.wait_for_timeout(2000)
            continue
        except Exception as e:
            logger.error(f"Indeed.nl error on attempt {attempt + 1}/{retries}: {str(e)}")
            continue

    return jobs

async def scrape_iamexpat_nl(page: Page, retries: int = 2) -> List[Dict]:
    """Scrape IamExpat.nl with retries"""
    logger.info("Scraping IamExpat.nl...")
    jobs = []

    for attempt in range(retries):
        try:
            url = "https://www.iamexpat.nl/jobs?search=risk&country=Netherlands"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            # Try multiple selectors
            selectors = ['div.job-result', 'div[class*="job"]', 'article']
            job_results = []

            for selector in selectors:
                job_results = await page.query_selector_all(selector)
                if job_results:
                    logger.info(f"Found {len(job_results)} with selector: {selector}")
                    break

            if not job_results:
                await page.wait_for_selector('div.job-result', timeout=20000)
                job_results = await page.query_selector_all('div.job-result')

            logger.info(f"Found {len(job_results)} job containers on IamExpat")

            for i, job in enumerate(job_results[:25]):
                try:
                    job_data = await job.evaluate("""
                        (el) => {
                            const title = el.querySelector('h3')?.textContent?.trim() || el.querySelector('h2')?.textContent?.trim() || 'N/A';
                            const company = el.querySelector('[class*="company"]')?.textContent?.trim() || 'N/A';
                            const salary = el.querySelector('[class*="salary"]')?.textContent?.trim() || 'Not listed';
                            const link = el.querySelector('a');
                            const url = link?.href || '';
                            return { title, company, salary, url };
                        }
                    """)

                    if job_data['title'] != 'N/A' and job_data['url']:
                        jobs.append({
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'location': "Netherlands",
                            'salary': job_data['salary'],
                            'url': job_data['url'],
                            'source': 'IamExpat.nl',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error extracting IamExpat job {i}: {str(e)}")
                    continue

            logger.info(f"IamExpat.nl: Found {len(jobs)} jobs (attempt {attempt + 1})")
            if jobs:
                return jobs

        except PlaywrightTimeoutError as e:
            logger.warning(f"IamExpat.nl timeout on attempt {attempt + 1}/{retries}")
            await page.wait_for_timeout(2000)
            continue
        except Exception as e:
            logger.error(f"IamExpat.nl error on attempt {attempt + 1}/{retries}: {str(e)}")
            continue

    return jobs

async def scrape_undutchables(page: Page, retries: int = 2) -> List[Dict]:
    """Scrape Undutchables with retries"""
    logger.info("Scraping Undutchables...")
    jobs = []

    for attempt in range(retries):
        try:
            url = "https://www.undutchables.com/jobs?q=risk&country=Netherlands"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            selectors = ['div.job-result', 'div[class*="job"]', 'article']
            job_results = []

            for selector in selectors:
                job_results = await page.query_selector_all(selector)
                if job_results:
                    break

            logger.info(f"Found {len(job_results)} job containers on Undutchables")

            for i, job in enumerate(job_results[:25]):
                try:
                    job_data = await job.evaluate("""
                        (el) => {
                            const title = el.querySelector('h2')?.textContent?.trim() || el.querySelector('h3')?.textContent?.trim() || 'N/A';
                            const company = el.querySelector('[class*="company"]')?.textContent?.trim() || 'N/A';
                            const salary = el.querySelector('[class*="salary"]')?.textContent?.trim() || 'Not listed';
                            const link = el.querySelector('a');
                            const url = link?.href || '';
                            return { title, company, salary, url };
                        }
                    """)

                    if job_data['title'] != 'N/A' and job_data['url']:
                        if not job_data['url'].startswith('http'):
                            job_data['url'] = f"https://www.undutchables.com{job_data['url']}"

                        jobs.append({
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'location': "Netherlands",
                            'salary': job_data['salary'],
                            'url': job_data['url'],
                            'source': 'Undutchables',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error extracting Undutchables job {i}: {str(e)}")
                    continue

            logger.info(f"Undutchables: Found {len(jobs)} jobs (attempt {attempt + 1})")
            if jobs:
                return jobs

        except PlaywrightTimeoutError as e:
            logger.warning(f"Undutchables timeout on attempt {attempt + 1}/{retries}")
            await page.wait_for_timeout(2000)
            continue
        except Exception as e:
            logger.error(f"Undutchables error on attempt {attempt + 1}/{retries}: {str(e)}")
            continue

    return jobs

async def scrape_monsterboard_nl(page: Page, retries: int = 2) -> List[Dict]:
    """Scrape Monsterboard.nl with retries"""
    logger.info("Scraping Monsterboard.nl...")
    jobs = []

    for attempt in range(retries):
        try:
            url = "https://www.monsterboard.nl/en/jobs/risk-analyst/in-netherlands"
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(3000)

            selectors = ['div.job-listing', 'div[class*="job"]', 'article']
            job_listings = []

            for selector in selectors:
                job_listings = await page.query_selector_all(selector)
                if job_listings:
                    break

            logger.info(f"Found {len(job_listings)} job containers on Monsterboard")

            for i, job in enumerate(job_listings[:25]):
                try:
                    job_data = await job.evaluate("""
                        (el) => {
                            const title = el.querySelector('h2')?.textContent?.trim() || 'N/A';
                            const company = el.querySelector('[class*="company"]')?.textContent?.trim() || 'N/A';
                            const salary = el.querySelector('[class*="salary"]')?.textContent?.trim() || 'Not listed';
                            const link = el.querySelector('a');
                            const url = link?.href || '';
                            return { title, company, salary, url };
                        }
                    """)

                    if job_data['title'] != 'N/A' and job_data['url']:
                        jobs.append({
                            'title': job_data['title'],
                            'company': job_data['company'],
                            'location': "Netherlands",
                            'salary': job_data['salary'],
                            'url': job_data['url'],
                            'source': 'Monsterboard.nl',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.debug(f"Error extracting Monsterboard job {i}: {str(e)}")
                    continue

            logger.info(f"Monsterboard.nl: Found {len(jobs)} jobs (attempt {attempt + 1})")
            if jobs:
                return jobs

        except PlaywrightTimeoutError as e:
            logger.warning(f"Monsterboard.nl timeout on attempt {attempt + 1}/{retries}")
            await page.wait_for_timeout(2000)
            continue
        except Exception as e:
            logger.error(f"Monsterboard.nl error on attempt {attempt + 1}/{retries}: {str(e)}")
            continue

    return jobs

# ════════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ════════════════════════════════════════════════════════════════════════════════

async def run_all_scrapers() -> List[Dict]:
    """Run all scrapers with improved resilience"""
    logger.info("=" * 80)
    logger.info(f"Job Search Scraper v2 Started: {datetime.now().isoformat()}")
    logger.info("=" * 80)

    all_jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        page.set_default_timeout(60000)  # 60 seconds
        page.set_default_navigation_timeout(60000)

        try:
            scrapers = [
                ("Indeed.nl", lambda: scrape_indeed_nl(page)),
                ("IamExpat.nl", lambda: scrape_iamexpat_nl(page)),
                ("Undutchables", lambda: scrape_undutchables(page)),
                ("Monsterboard.nl", lambda: scrape_monsterboard_nl(page)),
            ]

            for name, scraper_func in scrapers:
                try:
                    jobs = await scraper_func()
                    all_jobs.extend(jobs)
                    await page.wait_for_timeout(2000)
                except Exception as e:
                    logger.error(f"Fatal error in {name}: {str(e)}")
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
    jobs = asyncio.run(run_all_scrapers())
    print(f"\n✓ Scraped {len(jobs)} jobs from 4 portals")
    print(f"  Output: jobs_scraped_*.json")
