# import streamlit as st
# import pandas as pd
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
# from time import sleep
# from random import uniform
# import os
# import sys
# import logging
# from urllib.parse import urljoin, urlparse
# from collections import deque

# # Set up logging
# logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
#                     format='%(asctime)s - %(message)s', encoding='utf-8')
# def safe_log(message):
#     logging.info(message)
#     try:
#         print(message)
#     except UnicodeEncodeError:
#         safe_message = message.encode('ascii', 'replace').decode('ascii')
#         print(safe_message)

# # Initialize WebDriver with minimal options for speed
# def initialize_driver():
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--headless")  # Run in headless mode for speed
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

# # Function to scrape emails from a website by crawling all accessible pages
# def scrape_emails(driver, website):
#     if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
#         return 'N/A'
    
#     website = website.strip()
#     if not (website.startswith('http://') or website.startswith('https://')):
#         website = f'https://{website}'
    
#     # Enhanced email pattern to catch various formats
#     email_pattern = re.compile(
#         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
#         re.IGNORECASE
#     )
#     emails = set()
    
#     # Parse base URL
#     parsed_base = urlparse(website)
#     base_domain = parsed_base.netloc
#     base_scheme = parsed_base.scheme
    
#     # Queue for BFS crawling
#     to_visit = deque([website])
#     visited = set()
#     max_pages = 10  # Limit to avoid excessive crawling
#     max_depth = 3   # Limit depth to prevent deep crawling
    
#     while to_visit and len(visited) < max_pages:
#         current_url = to_visit.popleft()
#         if current_url in visited:
#             continue
            
#         try:
#             safe_log(f'Accessing {current_url}')
#             driver.get(current_url)
#             WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
#             sleep(uniform(0.5, 1))
            
#             # Extract emails from page source
#             page_source = driver.page_source
#             found_emails = email_pattern.findall(page_source)
#             emails.update(found_emails)
            
#             # Extract emails from visible text
#             try:
#                 body_text = driver.find_element(By.TAG_NAME, 'body').text
#                 found_emails = email_pattern.findall(body_text)
#                 emails.update(found_emails)
#             except NoSuchElementException:
#                 pass
            
#             # Extract emails from meta tags and other attributes
#             try:
#                 elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
#                 for elem in elements:
#                     for attr in elem.get_property('attributes'):
#                         value = elem.get_attribute(attr['name'])
#                         if value:
#                             found_emails = email_pattern.findall(value)
#                             emails.update(found_emails)
#             except Exception:
#                 pass
            
#             if emails:
#                 safe_log(f'Found emails on {current_url}: {emails}')
#                 break  # Stop crawling if emails are found
            
#             # Find all internal links to crawl
#             try:
#                 links = driver.find_elements(By.TAG_NAME, 'a')
#                 for link in links:
#                     href = link.get_attribute('href')
#                     if href:
#                         href = urljoin(current_url, href)
#                         parsed_href = urlparse(href)
#                         if (parsed_href.netloc == base_domain and 
#                             parsed_href.scheme in ['http', 'https'] and
#                             href not in visited and
#                             href not in to_visit):
#                             # Check depth
#                             path_segments = len(parsed_href.path.strip('/').split('/'))
#                             if path_segments <= max_depth:
#                                 to_visit.append(href)
#             except Exception:
#                 pass
            
#             visited.add(current_url)
#             safe_log(f'Visited {len(visited)}/{max_pages} pages')
            
#         except (TimeoutException, WebDriverException) as e:
#             safe_log(f'Error accessing {current_url}: {str(e)}')
#             visited.add(current_url)
#             continue
    
#     return list(emails)[0] if emails else 'N/A'

# # Streamlit app
# def main():
#     st.title("Email Scraper from Websites")
#     st.write("Upload an Excel or CSV file containing website URLs to scrape emails.")
    
#     # File upload
#     uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
#     if uploaded_file:
#         # Read the file
#         try:
#             if uploaded_file.name.endswith('.xlsx'):
#                 df = pd.read_excel(uploaded_file, dtype=str)
#             else:
#                 df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
#             st.write("Uploaded file preview:")
#             st.dataframe(df.head())
#         except Exception as e:
#             st.error(f"Error reading file: {e}")
#             return
        
#         # Identify website column automatically
#         website_columns = [
#             col for col in df.columns 
#             if col.lower() in ['url', 'website', 'web', 'site'] and
#             not any(exclude in col.lower() for exclude in ['detail', 'page'])
#         ]
#         if not website_columns:
#             st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
#             return
        
#         selected_column = website_columns[0]  # Pick the first matching column
#         st.write(f"Using column '{selected_column}' for scraping emails.")
        
#         if st.button("Start Scraping"):
#             driver = initialize_driver()
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             # Initialize Email column if not exists
#             if 'Email' not in df.columns:
#                 df['Email'] = 'N/A'
            
#             try:
#                 total_rows = len(df)
#                 for index, row in df.iterrows():
#                     website = row[selected_column]
#                     status_text.text(f"Scraping email for {website} ({index+1}/{total_rows})")
#                     email = scrape_emails(driver, website)
#                     df.at[index, 'Email'] = email
#                     progress_bar.progress((index + 1) / total_rows)
                
#                 # Save the updated file
#                 output_filename = f"updated_{uploaded_file.name}"
#                 if uploaded_file.name.endswith('.xlsx'):
#                     df.to_excel(output_filename, index=False)
#                 else:
#                     df.to_csv(output_filename, index=False, encoding='utf-8')
                
#                 st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
#                 # Provide download button
#                 with open(output_filename, 'rb') as f:
#                     st.download_button(
#                         label="Download Updated File",
#                         data=f,
#                         file_name=output_filename,
#                         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
#                     )
                
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#             finally:
#                 driver.quit()
#                 status_text.text("Driver closed.")

# if __name__ == "__main__":
#     main()



# import streamlit as st
# import pandas as pd
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
# from time import sleep
# from random import uniform
# import os
# import sys
# import logging
# from urllib.parse import urljoin, urlparse
# from collections import deque

# # Set up logging
# logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
#                     format='%(asctime)s - %(message)s', encoding='utf-8')
# def safe_log(message):
#     logging.info(message)
#     try:
#         print(message)
#     except UnicodeEncodeError:
#         safe_message = message.encode('ascii', 'replace').decode('ascii')
#         print(safe_message)

# # Initialize WebDriver with minimal options for speed
# def initialize_driver():
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--headless")  # Run in headless mode for speed
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

# # Function to scrape emails from a website by crawling all accessible pages
# def scrape_emails(driver, website):
#     if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
#         return 'N/A'
    
#     website = website.strip()
#     if not (website.startswith('http://') or website.startswith('https://')):
#         website = f'https://{website}'
    
#     # Enhanced email pattern to catch various formats
#     email_pattern = re.compile(
#         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
#         re.IGNORECASE
#     )
#     emails = set()
    
#     # Parse base URL
#     parsed_base = urlparse(website)
#     base_domain = parsed_base.netloc
#     base_scheme = parsed_base.scheme
    
#     # Queue for BFS crawling
#     to_visit = deque([website])
#     visited = set()
#     max_pages = 10  # Limit to avoid excessive crawling
#     max_depth = 3   # Limit depth to prevent deep crawling
    
#     while to_visit and len(visited) < max_pages:
#         current_url = to_visit.popleft()
#         if current_url in visited:
#             continue
            
#         try:
#             safe_log(f'Accessing {current_url}')
#             driver.get(current_url)
#             WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
#             sleep(uniform(0.5, 1))
            
#             # Extract emails from page source
#             page_source = driver.page_source
#             found_emails = email_pattern.findall(page_source)
#             emails.update(found_emails)
            
#             # Extract emails from visible text
#             try:
#                 body_text = driver.find_element(By.TAG_NAME, 'body').text
#                 found_emails = email_pattern.findall(body_text)
#                 emails.update(found_emails)
#             except NoSuchElementException:
#                 pass
            
#             # Extract emails from meta tags and other attributes
#             try:
#                 elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
#                 for elem in elements:
#                     for attr in elem.get_property('attributes'):
#                         value = elem.get_attribute(attr['name'])
#                         if value:
#                             found_emails = email_pattern.findall(value)
#                             emails.update(found_emails)
#             except Exception:
#                 pass
            
#             if emails:
#                 safe_log(f'Found emails on {current_url}: {emails}')
#                 break  # Stop crawling if emails are found
            
#             # Find all internal links to crawl
#             try:
#                 links = driver.find_elements(By.TAG_NAME, 'a')
#                 for link in links:
#                     href = link.get_attribute('href')
#                     if href:
#                         href = urljoin(current_url, href)
#                         parsed_href = urlparse(href)
#                         if (parsed_href.netloc == base_domain and 
#                             parsed_href.scheme in ['http', 'https'] and
#                             href not in visited and
#                             href not in to_visit):
#                             # Check depth
#                             path_segments = len(parsed_href.path.strip('/').split('/'))
#                             if path_segments <= max_depth:
#                                 to_visit.append(href)
#             except Exception:
#                 pass
            
#             visited.add(current_url)
#             safe_log(f'Visited {len(visited)}/{max_pages} pages')
            
#         except (TimeoutException, WebDriverException) as e:
#             safe_log(f'Error accessing {current_url}: {str(e)}')
#             visited.add(current_url)
#             continue
    
#     return list(emails)[0] if emails else 'N/A'

# # Streamlit app
# def main():
#     st.title("Email Scraper from Websites")
#     st.write("Upload an Excel or CSV file containing website URLs to scrape emails.")
    
#     # File upload
#     uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
#     if uploaded_file:
#         # Read the file
#         try:
#             if uploaded_file.name.endswith('.xlsx'):
#                 df = pd.read_excel(uploaded_file, dtype=str)
#             else:
#                 df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
#             st.write("Uploaded file preview:")
#             st.dataframe(df.head())
#         except Exception as e:
#             st.error(f"Error reading file: {e}")
#             return
        
#         # Identify website column automatically
#         website_columns = [
#             col for col in df.columns 
#             if col.lower() in ['url', 'website', 'web', 'site', 'companyurl'] and
#             not any(exclude in col.lower() for exclude in ['detail', 'page'])
#         ]
#         if not website_columns:
#             st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
#             return
        
#         selected_column = website_columns[0]  # Pick the first matching column
#         st.write(f"Using column '{selected_column}' for scraping emails.")
        
#         if st.button("Start Scraping"):
#             driver = initialize_driver()
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             # Initialize Final Email column if not exists
#             if 'Final Email' not in df.columns:
#                 df['Final Email'] = 'N/A'
            
#             try:
#                 total_rows = len(df)
#                 for index, row in df.iterrows():
#                     website = row[selected_column]
#                     status_text.text(f"Scraping email for {website} ({index+1}/{total_rows})")
#                     email = scrape_emails(driver, website)
#                     df.at[index, 'Final Email'] = email
#                     progress_bar.progress((index + 1) / total_rows)
                
#                 # Save the updated file
#                 output_filename = f"updated_{uploaded_file.name}"
#                 if uploaded_file.name.endswith('.xlsx'):
#                     df.to_excel(output_filename, index=False)
#                 else:
#                     df.to_csv(output_filename, index=False, encoding='utf-8')
                
#                 st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
#                 # Provide download button
#                 with open(output_filename, 'rb') as f:
#                     st.download_button(
#                         label="Download Updated File",
#                         data=f,
#                         file_name=output_filename,
#                         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
#                     )
                
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#             finally:
#                 driver.quit()
#                 status_text.text("Driver closed.")

# if __name__ == "__main__":
#     main()


# import streamlit as st
# import pandas as pd
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
# from time import sleep
# from random import uniform
# import os
# import sys
# import logging
# from urllib.parse import urljoin, urlparse
# from collections import deque

# # Set up logging
# logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
#                     format='%(asctime)s - %(message)s', encoding='utf-8')
# def safe_log(message):
#     logging.info(message)
#     try:
#         print(message)
#     except UnicodeEncodeError:
#         safe_message = message.encode('ascii', 'replace').decode('ascii')
#         print(safe_message)

# # Initialize WebDriver with minimal options for speed
# def initialize_driver():
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--headless")  # Run in headless mode for speed
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

# # Function to scrape emails from a website by crawling all accessible pages
# def scrape_emails(driver, website):
#     if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
#         return 'N/A'
    
#     website = website.strip()
#     if not (website.startswith('http://') or website.startswith('https://')):
#         website = f'https://{website}'
    
#     # Enhanced email pattern to catch various formats
#     email_pattern = re.compile(
#         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
#         re.IGNORECASE
#     )
#     emails = set()
    
#     # Parse base URL
#     parsed_base = urlparse(website)
#     base_domain = parsed_base.netloc
#     base_scheme = parsed_base.scheme
    
#     # Queue for BFS crawling
#     to_visit = deque([website])
#     visited = set()
#     max_pages = 10  # Limit to avoid excessive crawling
#     max_depth = 3   # Limit depth to prevent deep crawling
#     max_retries = 2  # Number of retry attempts per page
    
#     while to_visit and len(visited) < max_pages:
#         current_url = to_visit.popleft()
#         if current_url in visited:
#             continue
            
#         for attempt in range(max_retries):
#             try:
#                 safe_log(f'Accessing {current_url} (Attempt {attempt + 1}/{max_retries})')
#                 driver.get(current_url)
#                 WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
#                 sleep(uniform(0.5, 1))
                
#                 # Extract emails from page source
#                 page_source = driver.page_source
#                 found_emails = email_pattern.findall(page_source)
#                 emails.update(found_emails)
                
#                 # Extract emails from visible text
#                 try:
#                     body_text = driver.find_element(By.TAG_NAME, 'body').text
#                     found_emails = email_pattern.findall(body_text)
#                     emails.update(found_emails)
#                 except NoSuchElementException:
#                     pass
                
#                 # Extract emails from meta tags and other attributes
#                 try:
#                     elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
#                     for elem in elements:
#                         for attr in elem.get_property('attributes'):
#                             value = elem.get_attribute(attr['name'])
#                             if value:
#                                 found_emails = email_pattern.findall(value)
#                                 emails.update(found_emails)
#                 except Exception:
#                     pass
                
#                 if emails:
#                     safe_log(f'Found emails on {current_url}: {emails}')
#                     break  # Stop crawling if emails are found
                
#                 # Find all internal links to crawl
#                 try:
#                     links = driver.find_elements(By.TAG_NAME, 'a')
#                     for link in links:
#                         href = link.get_attribute('href')
#                         if href:
#                             href = urljoin(current_url, href)
#                             parsed_href = urlparse(href)
#                             if (parsed_href.netloc == base_domain and 
#                                 parsed_href.scheme in ['http', 'https'] and
#                                 href not in visited and
#                                 href not in to_visit):
#                                 # Check depth
#                                 path_segments = len(parsed_href.path.strip('/').split('/'))
#                                 if path_segments <= max_depth:
#                                     to_visit.append(href)
#                 except Exception:
#                     pass
                
#                 visited.add(current_url)
#                 safe_log(f'Visited {len(visited)}/{max_pages} pages')
#                 break  # Successful page load, exit retry loop
                
#             except (TimeoutException, WebDriverException) as e:
#                 safe_log(f'Error accessing {current_url} (Attempt {attempt + 1}/{max_retries}): {str(e)}')
#                 if attempt + 1 == max_retries:
#                     visited.add(current_url)
#                     safe_log(f'Failed to access {current_url} after {max_retries} attempts, skipping.')
#                 continue
    
#     return list(emails)[0] if emails else 'N/A'

# # Streamlit app
# def main():
#     st.title("Email Scraper from Websites")
#     st.write("Upload an Excel or CSV file containing website URLs to scrape emails.")
    
#     # File upload
#     uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
#     if uploaded_file:
#         # Read the file
#         try:
#             if uploaded_file.name.endswith('.xlsx'):
#                 df = pd.read_excel(uploaded_file, dtype=str)
#             else:
#                 df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
#             st.write("Uploaded file preview:")
#             st.dataframe(df.head())
#         except Exception as e:
#             st.error(f"Error reading file: {e}")
#             return
        
#         # Identify website column automatically
#         website_columns = [
#             col for col in df.columns 
#             if col.lower() in ['url', 'website', 'web', 'site'] and
#             not any(exclude in col.lower() for exclude in ['detail', 'page'])
#         ]
#         if not website_columns:
#             st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
#             return
        
#         selected_column = website_columns[0]  # Pick the first matching column
#         st.write(f"Using column '{selected_column}' for scraping emails.")
        
#         if st.button("Start Scraping"):
#             driver = initialize_driver()
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             # Initialize Final Email column if not exists
#             if 'Final Email' not in df.columns:
#                 df['Final Email'] = 'N/A'
            
#             try:
#                 total_rows = len(df)
#                 for index, row in df.iterrows():
#                     website = row[selected_column]
#                     status_text.text(f"Scraping email for {website} ({index+1}/{total_rows})")
#                     email = scrape_emails(driver, website)
#                     df.at[index, 'Final Email'] = email
#                     progress_bar.progress((index + 1) / total_rows)
                
#                 # Save the updated file
#                 output_filename = f"updated_{uploaded_file.name}"
#                 if uploaded_file.name.endswith('.xlsx'):
#                     df.to_excel(output_filename, index=False)
#                 else:
#                     df.to_csv(output_filename, index=False, encoding='utf-8')
                
#                 st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
#                 # Provide download button
#                 with open(output_filename, 'rb') as f:
#                     st.download_button(
#                         label="Download Updated File",
#                         data=f,
#                         file_name=output_filename,
#                         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
#                     )
                
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#             finally:
#                 driver.quit()
#                 status_text.text("Driver closed.")

# if __name__ == "__main__":
#     main()




# import streamlit as st
# import pandas as pd
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
# from time import sleep, time
# from random import uniform
# import os
# import sys
# import logging
# from urllib.parse import urljoin, urlparse
# from collections import deque

# # Set up logging
# logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
#                     format='%(asctime)s - %(message)s', encoding='utf-8')
# def safe_log(message):
#     logging.info(message)
#     try:
#         print(message)
#     except UnicodeEncodeError:
#         safe_message = message.encode('ascii', 'replace').decode('ascii')
#         print(safe_message)

# # Initialize WebDriver with minimal options for speed
# def initialize_driver():
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--headless")  # Run in headless mode for speed
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(options=chrome_options)
#     return driver

# # Function to scrape emails from a website by crawling all accessible pages
# def scrape_emails(driver, website):
#     if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
#         return 'N/A'
    
#     website = website.strip()
#     if not (website.startswith('http://') or website.startswith('https://')):
#         website = f'https://{website}'
    
#     # Enhanced email pattern to catch various formats
#     email_pattern = re.compile(
#         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
#         re.IGNORECASE
#     )
#     emails = set()
    
#     # Parse base URL
#     parsed_base = urlparse(website)
#     base_domain = parsed_base.netloc
#     base_scheme = parsed_base.scheme
    
#     # Queue for BFS crawling
#     to_visit = deque([website])
#     visited = set()
#     max_pages = 10  # Limit to avoid excessive crawling
#     max_depth = 3   # Limit depth to prevent deep crawling
#     max_retries = 2  # Number of retry attempts per page
    
#     while to_visit and len(visited) < max_pages:
#         current_url = to_visit.popleft()
#         if current_url in visited:
#             continue
            
#         for attempt in range(max_retries):
#             try:
#                 safe_log(f'Accessing {current_url} (Attempt {attempt + 1}/{max_retries})')
#                 driver.get(current_url)
#                 WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
#                 sleep(uniform(0.5, 1))
                
#                 # Extract emails from page source
#                 page_source = driver.page_source
#                 found_emails = email_pattern.findall(page_source)
#                 emails.update(found_emails)
                
#                 # Extract emails from visible text
#                 try:
#                     body_text = driver.find_element(By.TAG_NAME, 'body').text
#                     found_emails = email_pattern.findall(body_text)
#                     emails.update(found_emails)
#                 except NoSuchElementException:
#                     pass
                
#                 # Extract emails from meta tags and other attributes
#                 try:
#                     elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
#                     for elem in elements:
#                         for attr in elem.get_property('attributes'):
#                             value = elem.get_attribute(attr['name'])
#                             if value:
#                                 found_emails = email_pattern.findall(value)
#                                 emails.update(found_emails)
#                 except Exception:
#                     pass
                
#                 if emails:
#                     safe_log(f'Found emails on {current_url}: {emails}')
#                     break  # Stop crawling if emails are found
                
#                 # Find all internal links to crawl
#                 try:
#                     links = driver.find_elements(By.TAG_NAME, 'a')
#                     for link in links:
#                         href = link.get_attribute('href')
#                         if href:
#                             href = urljoin(current_url, href)
#                             parsed_href = urlparse(href)
#                             if (parsed_href.netloc == base_domain and 
#                                 parsed_href.scheme in ['http', 'https'] and
#                                 href not in visited and
#                                 href not in to_visit):
#                                 # Check depth
#                                 path_segments = len(parsed_href.path.strip('/').split('/'))
#                                 if path_segments <= max_depth:
#                                     to_visit.append(href)
#                 except Exception:
#                     pass
                
#                 visited.add(current_url)
#                 safe_log(f'Visited {len(visited)}/{max_pages} pages')
#                 break  # Successful page load, exit retry loop
                
#             except (TimeoutException, WebDriverException) as e:
#                 safe_log(f'Error accessing {current_url} (Attempt {attempt + 1}/{max_retries}): {str(e)}')
#                 if attempt + 1 == max_retries:
#                     visited.add(current_url)
#                     safe_log(f'Failed to access {current_url} after {max_retries} attempts, skipping.')
#                 continue
    
#     return list(emails)[0] if emails else 'N/A'

# # Streamlit app
# def main():
#     st.title("Email Scraper from Websites")
#     st.write("Upload an Excel or CSV file containing website URLs to scrape emails.")
    
#     # File upload
#     uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
#     if uploaded_file:
#         # Read the file
#         try:
#             if uploaded_file.name.endswith('.xlsx'):
#                 df = pd.read_excel(uploaded_file, dtype=str)
#             else:
#                 df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
#             st.write("Uploaded file preview:")
#             st.dataframe(df.head())
#         except Exception as e:
#             st.error(f"Error reading file: {e}")
#             return
        
#         # Identify website column automatically
#         website_columns = [
#             col for col in df.columns 
#             if col.lower() in ['url', 'website', 'web', 'site'] and
#             not any(exclude in col.lower() for exclude in ['detail', 'page'])
#         ]
#         if not website_columns:
#             st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
#             return
        
#         selected_column = website_columns[0]  # Pick the first matching column
#         st.write(f"Using column '{selected_column}' for scraping emails.")
        
#         if st.button("Start Scraping"):
#             driver = initialize_driver()
#             progress_bar = st.progress(0)
#             status_text = st.empty()
#             scrape_times = []  # List to store time taken per website
            
#             # Initialize Final Email column if not exists
#             if 'Final Email' not in df.columns:
#                 df['Final Email'] = 'N/A'
            
#             try:
#                 total_rows = len(df)
#                 for index, row in df.iterrows():
#                     website = row[selected_column]
#                     status_text.text(f"Scraping email for {website} ({index+1}/{total_rows})")
                    
#                     # Measure time for scraping this website
#                     start_time = time()
#                     email = scrape_emails(driver, website)
#                     end_time = time()
#                     scrape_time = end_time - start_time
#                     scrape_times.append(scrape_time)
                    
#                     df.at[index, 'Final Email'] = email
#                     progress_bar.progress((index + 1) / total_rows)
                
#                 # Calculate and display average scrape time
#                 avg_scrape_time = sum(scrape_times) / len(scrape_times) if scrape_times else 0
#                 st.write(f"Average time to scrape each website: {avg_scrape_time:.2f} seconds")
                
#                 # Save the updated file
#                 output_filename = f"updated_{uploaded_file.name}"
#                 if uploaded_file.name.endswith('.xlsx'):
#                     df.to_excel(output_filename, index=False)
#                 else:
#                     df.to_csv(output_filename, index=False, encoding='utf-8')
                
#                 st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
#                 # Provide download button
#                 with open(output_filename, 'rb') as f:
#                     st.download_button(
#                         label="Download Updated File",
#                         data=f,
#                         file_name=output_filename,
#                         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
#                     )
                
#             except Exception as e:
#                 st.error(f"An error occurred: {e}")
#             finally:
#                 driver.quit()
#                 status_text.text("Driver closed.")

# if __name__ == "__main__":
#     main()


# import streamlit as st
# import pandas as pd
# import re
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
# from time import sleep, time
# from random import uniform
# import os
# import sys
# import logging
# from urllib.parse import urljoin, urlparse
# from collections import deque

# # Set up logging
# logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
#                     format='%(asctime)s - %(message)s', encoding='utf-8')
# def safe_log(message):
#     logging.info(message)
#     try:
#         print(message)
#     except UnicodeEncodeError:
#         safe_message = message.encode('ascii', 'replace').decode('ascii')
#         print(safe_message)

# # Initialize WebDriver with minimal options for speed
# def initialize_driver():
#     chrome_options = webdriver.ChromeOptions()
#     chrome_options.add_argument("--headless")  # Run in headless mode for speed
#     chrome_options.add_argument("--disable-gpu")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")
#     chrome_options.add_argument("--log-level=3")
#     chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
#     driver = webdriver.Chrome(options=chrome_options)
#     driver.set_page_load_timeout(30)  # Set page load timeout to 30 seconds
#     return driver

# # Function to scrape emails from a website by crawling all accessible pages
# def scrape_emails(driver, website):
#     if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
#         return 'N/A'
    
#     website = website.strip()
#     if not (website.startswith('http://') or website.startswith('https://')):
#         website = f'https://{website}'
    
#     # Enhanced email pattern to catch various formats
#     email_pattern = re.compile(
#         r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
#         re.IGNORECASE
#     )
#     emails = set()
    
#     # Parse base URL
#     parsed_base = urlparse(website)
#     base_domain = parsed_base.netloc
#     base_scheme = parsed_base.scheme
    
#     # Queue for BFS crawling
#     to_visit = deque([website])
#     visited = set()
#     max_pages = 5   # Reduced to 5 to limit crawling time
#     max_depth = 3   # Limit depth to prevent deep crawling
#     max_retries = 2 # Number of retry attempts per page
    
#     while to_visit and len(visited) < max_pages:
#         current_url = to_visit.popleft()
#         if current_url in visited:
#             continue
            
#         for attempt in range(max_retries):
#             try:
#                 safe_log(f'Accessing {current_url} (Attempt {attempt + 1}/{max_retries})')
#                 driver.get(current_url)
#                 WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
#                 sleep(uniform(0.5, 1))
                
#                 # Extract emails from page source
#                 page_source = driver.page_source
#                 found_emails = email_pattern.findall(page_source)
#                 emails.update(found_emails)
                
#                 # Extract emails from visible text
#                 try:
#                     body_text = driver.find_element(By.TAG_NAME, 'body').text
#                     found_emails = email_pattern.findall(body_text)
#                     emails.update(found_emails)
#                 except NoSuchElementException:
#                     pass
                
#                 # Extract emails from meta tags and other attributes
#                 try:
#                     elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
#                     for elem in elements:
#                         for attr in elem.get_property('attributes'):
#                             value = elem.get_attribute(attr['name'])
#                             if value:
#                                 found_emails = email_pattern.findall(value)
#                                 emails.update(found_emails)
#                 except Exception:
#                     pass
                
#                 if emails:
#                     safe_log(f'Found emails on {current_url}: {emails}')
#                     break  # Stop crawling if emails are found
                
#                 # Find all internal links to crawl
#                 try:
#                     links = driver.find_elements(By.TAG_NAME, 'a')
#                     for link in links:
#                         href = link.get_attribute('href')
#                         if href:
#                             href = urljoin(current_url, href)
#                             parsed_href = urlparse(href)
#                             if (parsed_href.netloc == base_domain and 
#                                 parsed_href.scheme in ['http', 'https'] and
#                                 href not in visited and
#                                 href not in to_visit):
#                                 # Check depth
#                                 path_segments = len(parsed_href.path.strip('/').split('/'))
#                                 if path_segments <= max_depth:
#                                     to_visit.append(href)
#                 except Exception:
#                     pass
                
#                 visited.add(current_url)
#                 safe_log(f'Visited {len(visited)}/{max_pages} pages')
#                 break  # Successful page load, exit retry loop
                
#             except (TimeoutException, WebDriverException) as e:
#                 safe_log(f'Error accessing {current_url} (Attempt {attempt + 1}/{max_retries}): {str(e)}')
#                 if attempt + 1 == max_retries:
#                     visited.add(current_url)
#                     safe_log(f'Failed to access {current_url} after {max_retries} attempts, skipping.')
#                 continue
    
#     return list(emails)[0] if emails else 'N/A'

# # Streamlit app
# def main():
#     st.title("Email Scraper from Websites")
#     st.write("Upload an Excel or CSV file containing website URLs to scrape emails.")
    
#     # Initialize session state for keep-alive
#     if 'scraping' not in st.session_state:
#         st.session_state.scraping = False
    
#     # File upload
#     uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
#     if uploaded_file:
#         # Read the file
#         try:
#             if uploaded_file.name.endswith('.xlsx'):
#                 df = pd.read_excel(uploaded_file, dtype=str)
#             else:
#                 df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
#             st.write("Uploaded file preview:")
#             st.dataframe(df.head())
#         except Exception as e:
#             st.error(f"Error reading file: {e}")
#             return
        
#         # Identify website column automatically
#         website_columns = [
#             col for col in df.columns 
#             if col.lower() in ['url', 'website', 'web', 'site'] and
#             not any(exclude in col.lower() for exclude in ['detail', 'page'])
#         ]
#         if not website_columns:
#             st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
#             return
        
#         selected_column = website_columns[0]  # Pick the first matching column
#         st.write(f"Using column '{selected_column}' for scraping emails.")
        
#         if st.button("Start Scraping") and not st.session_state.scraping:
#             st.session_state.scraping = True
#             driver = initialize_driver()
#             progress_bar = st.progress(0)
#             status_text = st.empty()
#             scrape_times = []  # List to store time taken per website
            
#             # Initialize Final Email column if not exists
#             if 'Final Email' not in df.columns:
#                 df['Final Email'] = 'N/A'
            
#             try:
#                 total_rows = len(df)
#                 for index, row in df.iterrows():
#                     website = row[selected_column]
#                     status_text.text(f"Scraping email for {website} ({index+1}/{total_rows})")
                    
#                     # Measure time for scraping this website
#                     start_time = time()
#                     try:
#                         email = scrape_emails(driver, website)
#                     except Exception as e:
#                         safe_log(f"Unexpected error scraping {website}: {str(e)}")
#                         email = 'N/A'
#                         # Restart WebDriver if session is invalid
#                         if 'invalid session id' in str(e).lower():
#                             safe_log("Restarting WebDriver due to invalid session...")
#                             driver.quit()
#                             driver = initialize_driver()
#                     end_time = time()
#                     scrape_time = end_time - start_time
#                     scrape_times.append(scrape_time)
                    
#                     df.at[index, 'Final Email'] = email
#                     progress_bar.progress((index + 1) / total_rows)
#                     sleep(0.1)  # Short delay to reduce WebDriver load
                
#                 # Calculate and display average scrape time
#                 avg_scrape_time = sum(scrape_times) / len(scrape_times) if scrape_times else 0
#                 st.write(f"Average time to scrape each website: {avg_scrape_time:.2f} seconds")
                
#                 # Save the updated file
#                 output_filename = f"updated_{uploaded_file.name}"
#                 if uploaded_file.name.endswith('.xlsx'):
#                     df.to_excel(output_filename, index=False)
#                 else:
#                     df.to_csv(output_filename, index=False, encoding='utf-8')
                
#                 st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
#                 # Provide download button
#                 with open(output_filename, 'rb') as f:
#                     st.download_button(
#                         label="Download Updated File",
#                         data=f,
#                         file_name=output_filename,
#                         mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
#                     )
                
#             except Exception as e:
#                 st.error(f"An error occurred: {str(e)}")
#             finally:
#                 driver.quit()
#                 status_text.text("Driver closed.")
#                 st.session_state.scraping = False

# if __name__ == "__main__":
#     main()



import streamlit as st
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from time import sleep, time
from random import uniform
import os
import logging
from urllib.parse import urljoin, urlparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import threading
import numpy as np

# Set up thread-safe logging
logging.basicConfig(filename='email_scraper_log.txt', level=logging.INFO, 
                    format='%(asctime)s - [%(threadName)s] - %(message)s', encoding='utf-8')
logger_lock = threading.Lock()

def safe_log(message):
    with logger_lock:
        logging.info(message)
        try:
            print(message)
        except UnicodeEncodeError:
            safe_message = message.encode('ascii', 'replace').decode('ascii')
            print(safe_message)

# Initialize WebDriver with minimal options for speed
def initialize_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(45)
    return driver

# Function to scrape emails from a website
def scrape_emails(website, thread_name="MainThread"):
    if pd.isna(website) or website == 'N/A' or not isinstance(website, str):
        return 'N/A'
    
    website = website.strip()
    if not (website.startswith('http://') or website.startswith('https://')):
        website = f'https://{website}'
    
    email_pattern = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    emails = set()
    
    parsed_base = urlparse(website)
    base_domain = parsed_base.netloc
    base_scheme = parsed_base.scheme
    
    to_visit = deque([website])
    visited = set()
    max_pages = 10
    max_depth = 2
    max_retries = 2
    
    driver = initialize_driver()
    try:
        while to_visit and len(visited) < max_pages:
            current_url = to_visit.popleft()
            if current_url in visited:
                continue
                
            for attempt in range(max_retries):
                try:
                    safe_log(f'[{thread_name}] Accessing {current_url} (Attempt {attempt + 1}/{max_retries})')
                    driver.get(current_url)
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    sleep(uniform(0.5, 1))
                    
                    page_source = driver.page_source
                    found_emails = email_pattern.findall(page_source)
                    emails.update(found_emails)
                    
                    try:
                        body_text = driver.find_element(By.TAG_NAME, 'body').text
                        found_emails = email_pattern.findall(body_text)
                        emails.update(found_emails)
                    except NoSuchElementException:
                        pass
                    
                    try:
                        elements = driver.find_elements(By.XPATH, '//*[@*[contains(., "@")]]')
                        for elem in elements:
                            for attr in elem.get_property('attributes'):
                                value = elem.get_attribute(attr['name'])
                                if value:
                                    found_emails = email_pattern.findall(value)
                                    emails.update(found_emails)
                    except Exception:
                        pass
                    
                    if emails:
                        safe_log(f'[{thread_name}] Found emails on {current_url}: {emails}')
                        break
                    
                    try:
                        links = driver.find_elements(By.TAG_NAME, 'a')
                        for link in links:
                            href = link.get_attribute('href')
                            if href:
                                href = urljoin(current_url, href)
                                parsed_href = urlparse(href)
                                if (parsed_href.netloc == base_domain and 
                                    parsed_href.scheme in ['http', 'https'] and
                                    href not in visited and
                                    href not in to_visit):
                                    path_segments = len(parsed_href.path.strip('/').split('/'))
                                    if path_segments <= max_depth:
                                        to_visit.append(href)
                    except Exception:
                        pass
                    
                    visited.add(current_url)
                    safe_log(f'[{thread_name}] Visited {len(visited)}/{max_pages} pages')
                    break
                    
                except (TimeoutException, WebDriverException) as e:
                    safe_log(f'[{thread_name}] Error accessing {current_url} (Attempt {attempt + 1}/{max_retries}): {str(e)}')
                    if attempt + 1 == max_retries:
                        visited.add(current_url)
                        safe_log(f'[{thread_name}] Failed to access {current_url} after {max_retries} attempts, skipping.')
                    continue
    finally:
        driver.quit()
        safe_log(f'[{thread_name}] WebDriver closed.')
    
    return list(emails)[0] if emails else 'N/A'

# Function to process a batch of websites in parallel
def process_batch(batch_df, selected_column, batch_index, total_batches, status_text, progress_bar, total_rows, processed_rows, scrape_times):
    results = []
    batch_df = batch_df.copy()  # Ensure we work on a copy to avoid index issues
    with ThreadPoolExecutor(max_workers=8) as executor:  # Reduced to 8 for 8GB RAM
        future_to_index = {
            executor.submit(scrape_emails, row[selected_column], f"Thread-B{batch_index}-W{idx}"): idx
            for idx, (_, row) in enumerate(batch_df.iterrows())
        }
        
        for future in future_to_index:
            idx = future_to_index[future]
            start_time = time()
            try:
                email = future.result()
            except Exception as e:
                safe_log(f'[Thread-B{batch_index}-W{idx}] Unexpected error scraping {batch_df.at[batch_df.index[idx], selected_column]}: {str(e)}')
                email = 'N/A'
            end_time = time()
            
            with logger_lock:
                scrape_times.append(end_time - start_time)
                batch_df.at[batch_df.index[idx], 'Final Email'] = email
                processed_rows[0] += 1
                status_text.text(f"Processing batch {batch_index + 1}/{total_batches} - Scraped {processed_rows[0]}/{total_rows} websites")
                progress_bar.progress(processed_rows[0] / total_rows)
            
            results.append((idx, email))
    
    return batch_df

# Streamlit app
def main():
    st.title("Email Scraper from Websites (Parallel Batch Processing)")
    st.write("Upload an Excel or CSV file containing website URLs to scrape emails in batches of 10.")
    
    if 'scraping' not in st.session_state:
        st.session_state.scraping = False
    
    uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file, dtype=str)
            else:
                df = pd.read_csv(uploaded_file, dtype=str, encoding='utf-8')
            st.write("Uploaded file preview:")
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Error reading file: {e}")
            return
        
        website_columns = [
            col for col in df.columns 
            if col.lower() in ['url', 'website', 'web', 'site'] and
            not any(exclude in col.lower() for exclude in ['detail', 'page'])
        ]
        if not website_columns:
            st.error("No suitable columns found (e.g., 'URL', 'Website', 'Web', 'Site') without 'detail' or 'page' in the name.")
            return
        
        selected_column = website_columns[0]
        st.write(f"Using column '{selected_column}' for scraping emails.")
        
        if st.button("Start Scraping") and not st.session_state.scraping:
            st.session_state.scraping = True
            progress_bar = st.progress(0)
            status_text = st.empty()
            scrape_times = []
            processed_rows = [0]
            
            if 'Final Email' not in df.columns:
                df['Final Email'] = 'N/A'
            
            try:
                batch_size = 100
                total_rows = len(df)
                total_batches = (total_rows + batch_size - 1) // batch_size
                
                for batch_index in range(total_batches):
                    start_idx = batch_index * batch_size
                    end_idx = min(start_idx + batch_size, total_rows)
                    batch_df = df.iloc[start_idx:end_idx].copy()  # Use iloc for precise slicing
                    
                    status_text.text(f"Processing batch {batch_index + 1}/{total_batches} - Scraped {processed_rows[0]}/{total_rows} websites")
                    batch_df = process_batch(batch_df, selected_column, batch_index, total_batches, status_text, progress_bar, total_rows, processed_rows, scrape_times)
                    
                    # Update only the 'Final Email' column to avoid shape mismatch
                    df.loc[df.index[start_idx:end_idx], 'Final Email'] = batch_df['Final Email'].values
                    
                    sleep(0.2)  # Reduced delay for faster processing
                
                avg_scrape_time = sum(scrape_times) / len(scrape_times) if scrape_times else 0
                st.write(f"Average time to scrape each website: {avg_scrape_time:.2f} seconds")
                
                output_filename = f"updated_{uploaded_file.name}"
                if uploaded_file.name.endswith('.xlsx'):
                    df.to_excel(output_filename, index=False)
                else:
                    df.to_csv(output_filename, index=False, encoding='utf-8')
                
                st.success(f"Scraping completed! Updated file saved as {output_filename}")
                
                with open(output_filename, 'rb') as f:
                    st.download_button(
                        label="Download Updated File",
                        data=f,
                        file_name=output_filename,
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' if output_filename.endswith('.xlsx') else 'text/csv'
                    )
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                safe_log(f"Main loop error: {str(e)}")
            finally:
                status_text.text("Scraping completed.")
                st.session_state.scraping = False

if __name__ == "__main__":
    main()