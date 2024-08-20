class YellowPagesScraper:
    def __init__(self):
        self.url = "https://listing.yellowpages.com.sg/"

    def scrape_data(self, search_term, max_pages, headless_mode):
        data = []
        page_count = 0
        max_page_reached = False

        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-popup-blocking")
        
        if headless_mode:
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")

        user_agent = UserAgent().random
        chrome_options.add_argument(f"user-agent={user_agent}")

        driver = webdriver.Chrome(options=chrome_options)
        try:
            driver.get(self.url)
            search_box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "s")))
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 3))

            while page_count < max_pages:
                # Detect CAPTCHA
                try:
                    captcha_element = driver.find_element(By.CSS_SELECTOR, ".captcha")
                    if captcha_element.is_displayed():
                        print("CAPTCHA detected. Please solve it manually.")
                        input("Press Enter after solving the CAPTCHA...")
                        driver.refresh()
                        time.sleep(random.uniform(2, 3))
                        continue
                except NoSuchElementException:
                    pass

                # Close cookie notice if present
                try:
                    cookie_notice_close = driver.find_element(By.CSS_SELECTOR, "div.cookie-notice-container button.close")
                    if cookie_notice_close.is_displayed():
                        cookie_notice_close.click()
                        time.sleep(random.uniform(1, 2))
                except NoSuchElementException:
                    pass

                # Wait for listings to load
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "listing")))

                listings = driver.find_elements(By.CLASS_NAME, "listing")
                for listing in listings:
                    name = listing.find_element(By.TAG_NAME, "h2").text.strip() if listing.find_elements(By.TAG_NAME, "h2") else ""
                    
                    address = ""
                    address_selectors = ["address", ".location", ".address", "[itemprop='address']"]
                    for selector in address_selectors:
                        try:
                            address_elem = listing.find_element(By.CSS_SELECTOR, selector)
                            address = address_elem.text.strip()
                            if address:
                                break
                        except NoSuchElementException:
                            continue

                    phone = ""
                    phone_selectors = ["a.phone", ".phone", "[itemprop='telephone']", "[data-tracking='phone']"]
                    for selector in phone_selectors:
                        try:
                            phone_elem = listing.find_element(By.CSS_SELECTOR, selector)
                            phone = phone_elem.text.strip()
                            if not phone:
                                href = phone_elem.get_attribute("href")
                                if href and href.startswith("tel:"):
                                    phone = href[4:]
                            if phone:
                                break
                        except NoSuchElementException:
                            continue

                    website = ""
                    website_selectors = ["a.website", ".website", "[itemprop='url']", "[data-tracking='website']"]
                    for selector in website_selectors:
                        try:
                            website_elem = listing.find_element(By.CSS_SELECTOR, selector)
                            website = website_elem.get_attribute("href")
                            if website:
                                break
                        except NoSuchElementException:
                            continue

                    data.append({
                        "Name": name,
                        "Address": address,
                        "Phone": phone,
                        "Website": website
                    })

                page_count += 1
                if page_count >= max_pages:
                    break

                try:
                    next_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.next"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    next_button.click()
                    time.sleep(random.uniform(2, 3))
                except (NoSuchElementException, TimeoutException):
                    max_page_reached = True
                    break

        finally:
            driver.quit()
        
        return data, max_page_reached