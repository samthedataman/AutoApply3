import streamlit as st
import pandas as pd
import time
import random
import re
import math
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import streamlit as st
from urllib.parse import parse_qs, urlparse


def get_query_params():
    """Parse query parameters from the URL."""
    query_string = urlparse(st.experimental_get_query_params()).query
    return parse_qs(query_string)


browserstack_username = st.secrets["browserstack"]["username"]
browserstack_access_key = st.secrets["browserstack"]["access_key"]


def get_driver():
    desired_cap = {
        "os": "Windows",
        "os_version": "10",
        "browser": "Chrome",
        "browser_version": "latest",
        "name": "Dice Job Scraper Test",
    }

    driver = webdriver.Remote(
        command_executor=f"https://{browserstack_username}:{browserstack_access_key}@hub-cloud.browserstack.com/wd/hub",
        desired_capabilities=desired_cap,
    )
    return driver


def test_browserstack_setup():
    st.write("Testing BrowserStack setup...")
    try:
        driver = get_driver()
        if not driver:
            st.error("Failed to initialize WebDriver.")
            return False

        # Navigate to a simple, stable website
        driver.get("https://www.example.com")

        # Check if the title is correct
        if driver.title == "Example Domain":
            st.success("Successfully loaded example.com")
        else:
            st.warning(f"Loaded page, but title was unexpected: {driver.title}")

        # Try to find an element on the page
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            st.success(f"Found h1 element: {element.text}")
        except:
            st.error("Couldn't find h1 element on example.com")
            return False

        driver.quit()
        st.success("BrowserStack and Selenium are working correctly!")
        return True

    except Exception as e:
        st.error(f"An error occurred during the test: {str(e)}")
        return False


# Custom CSS for the Streamlit app
custom_css = """
<style>
    body {
        font-family: 'Segoe UI', sans-serif;
        background: linear-gradient(135deg, #1e1e2e 0%, #2a2a3c 100%);
        color: #e0e0e0;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .info-box {
        background: linear-gradient(45deg, #44475a 0%, #6272a4 100%);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button {
        background: linear-gradient(90deg, #bd93f9 0%, #ff79c6 100%);
        color: #1e1e2e;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
        border-radius: 25px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0,0,0,0.15);
    }
    .stTextInput > div > div > input, .stSelectbox > div > div > select, .stNumberInput > div > div > input {
        background-color: #383a59;
        color: #f8f8f2;
        border: 1px solid #6272a4;
        border-radius: 5px;
    }
    .stProgress > div > div > div {
        background-color: #ff79c6;
    }
    .stAlert {
        background-color: #44475a;
        color: #f8f8f2;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
</style>
"""

st.set_page_config(page_title="Dice Job Scraper", page_icon="🎲", layout="wide")
st.markdown(custom_css, unsafe_allow_html=True)

# User agent list for web scraping
user_agent_list = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1.1 Safari/605.1.15",
]


# Function to log into Dice.com and scrape job links
def get_job_links(driver, email, password, job_type, num_jobs, progress_bar):
    st.info("🔐 Logging in to Dice.com...")
    driver.get("https://www.dice.com/dashboard/login")

    try:
        # Enter email
        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="email"]'))
        )
        email_field.send_keys(email)
        st.info("✅ Email entered successfully.")

        # Click sign-in button
        sign_in_button = driver.find_element(
            By.XPATH, '//*[@data-testid="sign-in-button"]'
        )
        sign_in_button.click()
        st.info("✅ Sign-in button clicked. Waiting for password input...")

        # Enter password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@name="password"]'))
        )
        password_field.send_keys(password)
        st.info("✅ Password entered successfully.")

        # Submit password
        sign_in_button = driver.find_element(
            By.XPATH, '//*[@data-testid="submit-password"]'
        )
        sign_in_button.click()
        st.info("✅ Password submitted. Waiting for login to complete...")

        # Wait for login to complete
        time.sleep(5)  # Wait a fixed time instead of waiting for an element
        st.success("✅ Logged in successfully. Searching for jobs...")

    except TimeoutException:
        st.error("❌ Login failed. Please check your credentials and try again.")
        return []

    # Navigate to the job search page
    driver.get(f"https://www.dice.com/jobs/q-{job_type.replace(' ', '%20')}-jobs")
    time.sleep(5)  # Allow some time for the page to load
    st.info(
        f"🔍 Navigating to job search page: https://www.dice.com/jobs/q-{job_type.replace(' ', '%20')}-jobs"
    )

    # Get the total number of jobs available
    try:
        number_text = driver.execute_script(
            'return document.querySelector("span.p-reg-100").textContent;'
        )
        match = re.search(r"of (\d+,\d+)", number_text)
        total_jobs = int(match.group(1).replace(",", "")) if match else 300
        st.info(f"📊 Total jobs found: {total_jobs}")
    except Exception as e:
        st.warning("⚠️ Could not determine total number of jobs. Defaulting to 300.")
        total_jobs = 300

    jobs_to_scrape = min(num_jobs, total_jobs)
    pages_to_scrape = math.ceil(jobs_to_scrape / 20)
    st.info(f"📄 Will scrape {jobs_to_scrape} jobs from {pages_to_scrape} pages.")

    data_jobs_links = []

    for page in range(1, pages_to_scrape + 1):
        url = f"https://www.dice.com/jobs/q-{job_type.replace(' ', '%20')}-jobs?page={page}"
        driver.get(url)
        time.sleep(5)  # Allow some time for the page to load

        # Get job detail links using the existing scraping logic
        links = get_links_bs(url)
        data_jobs_links.extend(links)

        # Update the progress bar
        progress = page / pages_to_scrape
        progress_bar.progress(progress)
        st.info(f"🔄 Progress: {progress * 100:.2f}% - Scraped page {page}")

        time.sleep(random.uniform(1, 3))  # Random delay between requests

    st.success("🎉 Scraping finished!")
    return data_jobs_links


# Function to scrape job detail links
def get_links_bs(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    return [
        a["href"] for a in soup.find_all("a", href=True) if "job-detail" in a["href"]
    ]


# Function to apply for jobs
def apply_to_job(driver, link, email, password, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            st.info(f"🔗 Navigating to job link: {link}")
            driver.get(link)
            time.sleep(random.uniform(2, 4))

            # Find and click the apply button
            apply_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "apply-button-wc"))
            )
            driver.execute_script(
                "arguments[0].shadowRoot.querySelector('.btn.btn-primary').click();",
                apply_button,
            )
            st.info("✅ Clicked 'Apply' button.")

            time.sleep(random.uniform(2, 4))

            # Find and click the "Next" button
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.seds-button-primary.btn-next")
                )
            )
            next_button.click()
            st.info("✅ Clicked 'Next' button.")

            time.sleep(random.uniform(2, 4))

            # Find and click the "Submit" button
            submit_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[contains(@class, 'seds-button-primary') and contains(., 'Submit')]",
                    )
                )
            )
            submit_button.click()
            st.info("✅ Clicked 'Submit' button.")

            time.sleep(random.uniform(2, 4))
            return True

        except Exception as e:
            st.warning(
                f"⚠️ Error applying to job (attempt {attempt + 1}/{max_attempts}): {e}"
            )
            if attempt == max_attempts - 1:
                st.error("❌ Max attempts reached. Moving on to next job.")
                return False


# Main function to run the Streamlit app
def main():
    # Try to extract parameters with better error handling
    try:
        # Try to extract parameters from the query string
        query_params = st.query_params()

        # Extract individual parameters with default fallbacks
        email = query_params.get("email", [""])[0]
        user_id = query_params.get("user_id", [""])[0]
        access_token = query_params.get("access_token", [""])[0]
        credits = int(query_params.get("credits", ["0"])[0])
        username = query_params.get("username", [""])[0]
        job_title = query_params.get("job_title", [""])[0]
        avatar_url = query_params.get("avatar_url", [""])[0]

        # Display the extracted parameters if available
        st.title("🎲 Dice Job Scraper and Applicator")

        st.markdown(
            f"""
            <div style="text-align: center;">
                <h3>👤 {username} ({job_title})</h3>
                <p>Email: {email}</p>
                <p>Credits: {credits}</p>
                <img src="{avatar_url}" alt="Avatar" style="width:100px; border-radius:50%;"/>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception as e:
        # Handle any errors gracefully
        st.error("Failed to load user data. Please try again.")
        st.write(f"Error: {str(e)}")

    st.title("🎲 Dice Job Scraper and Applicator")

    st.markdown(
        """
    <div class="info-box">
        <h3>Welcome to the Dice Job Scraper!</h3>
        <p>This tool helps you automate your job search and application process on Dice.com. Simply enter your job preferences, and let the scraper do the work for you.</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if not email:
            email = st.text_input("✉️ Enter your Dice.com email:", key="email")
        password = st.text_input(
            "🔑 Enter your Dice.com password:", type="password", key="password"
        )

    with col2:
        job_type = st.text_input("🧑‍🏢 Enter Job Type:", key="job_type")
        num_jobs = st.number_input(
            "🔢 Number of jobs to apply:",
            min_value=1,
            max_value=1000,
            value=20,
            key="num_jobs",
        )

    if st.button("🚀 Start Job Scraping and Application", key="start_button"):
        if not email or not password or not job_type:
            st.error("❌ Please fill in all fields.")
            return

        st.write("🔨 Initializing WebDriver...")
        driver = get_driver()
        if not driver:
            st.error(
                "❌ Failed to initialize WebDriver. Please check your Chrome installation and try again."
            )
            return

        progress_bar = st.progress(0)
        st.write("🔍 Scraping job links...")
        job_links = get_job_links(
            driver, email, password, job_type, num_jobs, progress_bar
        )
        st.success(f"✅ Found {len(job_links)} job links.")

        st.write("✉️ Applying to jobs...")
        successful_applications = 0
        failed_applications = 0
        job_data = []

        for index, link in enumerate(job_links):
            st.write(f"💼 Applying to job {index + 1} of {len(job_links)}")
            time_applied = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            success = apply_to_job(driver, link, email, password)
            if success:
                successful_applications += 1
                st.success(f"✅ Successfully applied to job: {link}")
                job_data.append(
                    {
                        "Job Link": link,
                        "Job Title": job_type,
                        "Status": "Successful",
                        "Time Applied": time_applied,
                    }
                )
            else:
                failed_applications += 1
                st.warning(f"❌ Failed to apply to job: {link}")
                job_data.append(
                    {
                        "Job Link": link,
                        "Job Title": job_type,
                        "Status": "Failed",
                        "Time Applied": time_applied,
                    }
                )
            time.sleep(2)

        driver.quit()
        st.success("🎉 Job application process completed!")

        # Display cumulative bar chart of job applications
        st.subheader("📈 Cumulative Job Application Summary")
        chart_data = pd.DataFrame(
            {
                "Status": ["Successful Applications", "Failed Applications"],
                "Count": [successful_applications, failed_applications],
            }
        )
        st.bar_chart(chart_data.set_index("Status"))

        # Display a dataframe of job links, titles, statuses, and time applied
        st.subheader("📄 User Dashboard - Job Links and Application Status")
        job_df = pd.DataFrame(job_data)
        st.dataframe(job_df)

        st.markdown(
            f"""
        <div class="info-box">
            <h3>📋 Application Summary</h3>
            <p>✅ Successful applications: {successful_applications}</p>
            <p>❌ Failed applications: {failed_applications}</p>
            <p>📊 Total jobs processed: {len(job_links)}</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # Add a download button for the job links with additional information
        if job_data:
            job_df_csv = job_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Job Application Data",
                data=job_df_csv,
                file_name="job_application_data.csv",
                mime="text/csv",
            )


if __name__ == "__main__":
    main()
