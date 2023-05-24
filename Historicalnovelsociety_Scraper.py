from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService 
import undetected_chromedriver as uc
import pandas as pd
import time
import csv
import sys
import numpy as np
import re 

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # disabling images rendering 
    prefs = {"profile.managed_default_content_settings.images": 2}
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.page_load_strategy = 'eager'
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    chrome_service = ChromeService(driver_path)
    # configuring the driver
    driver = webdriver.Chrome(options=chrome_options, service=chrome_service)
    driver.set_page_load_timeout(60)
    driver.maximize_window()

    return driver

def scrape_historicalnovelsociety(path):

    start = time.time()
    print('-'*75)
    print('Scraping historicalnovelsociety.org ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame()

    # if no books links provided then get the links
    if path == '':
        name = 'historicalnovelsociety_data.xlsx'
        # getting the books under each category
        links = []
        nbooks, npages = 0, 0
        homepage = 'https://historicalnovelsociety.org/reviews/page/'
        while True:
            npages += 1
            url = homepage + str(npages)
            driver.get(url)
            # scraping books urls
            titles = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div[id='box_review_holder']")))
            for title in titles:
                try:
                    a = wait(title, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    nbooks += 1
                    print(f'Scraping the url for book {nbooks}')
                    link = a.get_attribute('href')
                    links.append(link)
                except Exception as err:
                    print('The below error occurred during the scraping from  historicalnovelsociety.com, retrying ..')
                    print('-'*50)
                    print(err)
                    continue

            # checking the next page
            try:
                button = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.next.page-numbers")))
            except:
                break
                    
        # saving the links to a csv file
        print('-'*75)
        print('Exporting links to a csv file ....')
        with open('historicalnovelsociety_links.csv', 'w', newline='\n', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Link'])
            for row in links:
                writer.writerow([row])

    scraped = []
    if path != '':
        df_links = pd.read_csv(path)
        name = path.split('\\')[-1][:-4]
        name = name + '_data.xlsx'
    else:
        df_links = pd.read_csv('historicalnovelsociety_links.csv')

    links = df_links['Link'].values.tolist()

    try:
        data = pd.read_excel(name)
        scraped = data['Title Link'].values.tolist()
    except:
        pass

    # scraping books details
    print('-'*75)
    print('Scraping Books Info...')
    print('-'*75)
    n = len(links)
    for i, link in enumerate(links):
        try:
            if link in scraped: continue
            driver.get(link)           
            details = {}
            print(f'Scraping the info for book {i+1}\{n}')

            # title and title link
            title_link, title = '', ''              
            try:
                title_link = link
                title = wait(driver, 2).until(EC.presence_of_element_located((By.TAG_NAME, "h1"))).get_attribute('textContent').replace('\n', '').strip().title() 
            except:
                print(f'Warning: failed to scrape the title for book: {link}')               
                
            details['Title'] = title
            details['Title Link'] = title_link                          
            # Author and reviewer
            author, author_link, reviewer, reviewer_link = '', '', '', ''
            try:
                p = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.author")))
                tags = wait(p, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                for tag in tags:
                    url = tag.get_attribute('href')
                    person = tag.get_attribute('textContent')
                    if '/by/' in url:
                        author += person + ', '
                        author_link += url + ', '
                    elif '/reviewer/' in url:
                        reviewer += person + ', '
                        reviewer_link += url + ', '
            except:
                pass
                    
            details['Author'] = author[:-2]            
            details['Author Link'] = author_link[:-2] 
            details['Reviewer'] = reviewer[:-2]            
            details['Reviewer Link'] = reviewer_link[:-2]             
            # publisher
            publisher = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.publisher_wrapper")))
                publisher = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Publisher'] = publisher            
            
            # genre
            genre = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.genre_wrapper")))
                tags = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                for tag in tags:
                    genre += tag.get_attribute('textContent').strip() + ', '
            except:
                pass          
                
            details['Genre'] = genre[:-2]             
                               
            # date
            pub_date = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.publish_year_wrapper")))
                pub_date = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Publication Date'] = pub_date                      
            # Amazon Link
            Amazon = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.amazon-box")))
                Amazon = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('href')
                if 'www.amazon' not in Amazon:
                    Amazon = ''
            except:
                pass          
                
            details['Amazon Link'] = Amazon              
            
            # Period
            period = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.period_wrapper")))
                period = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Period'] = period            
            
            # Century
            century = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.century_wrapper")))
                century = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Century'] = century              
            
            # Review date
            rev_date = ''
            try:
                div = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.mag_wrapper")))
                rev_date = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a"))).get_attribute('textContent').strip().split('(')[-1]
            except:
                pass          
                
            details['Review Date'] = rev_date[:-1] 

            # Review format & page count
            rev_format, rev_pages = '', ''
            try:
                divs = wait(driver, 2).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.isbn_wrapper")))
                for div in divs:
                    text = div.get_attribute('textContent')
                    if 'REVIEW FORMAT' in text:
                        rev_format = wait(div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.isbn_p"))).get_attribute('textContent').strip()
                    elif 'PAGE COUNT' in text:
                        rev_pages = wait(div, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "p.isbn_p"))).get_attribute('textContent').strip()
            except:
                pass          
                
            details['Review Format'] = rev_format   
            details['Review Pages'] = rev_pages            
                     
            # appending the output to the datafame       
            data = data.append([details.copy()])
            # saving data to csv file each 100 links
            if np.mod(i+1, 100) == 0:
                print('Outputting scraped data ...')
                data.to_excel(name, index=False)
        except Exception as err:
            print(str(err))
           

    # optional output to excel
    data.to_excel(name, index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'historicalnovelsociety.org scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":
    
    path = ''
    if len(sys.argv) == 2:
        path = sys.argv[1]
    data = scrape_historicalnovelsociety(path)

