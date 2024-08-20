import os
import sys
import platform
import subprocess
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pandas as pd
import time
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from fake_useragent import UserAgent

class WebsiteScraper:
    def __init__(self, url):
        self.url = url

    def scrape_data(self, search_term, max_pages, headless_mode):
        raise NotImplementedError("Subclass must implement abstract method")

class YellowPagesScraper(WebsiteScraper):
    def __init__(self):
        super().__init__("https://listing.yellowpages.com.sg/")

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
                        messagebox.showinfo("CAPTCHA Detected", "CAPTCHA detected. Please solve it manually and then click OK to continue.")
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

                    email = ""
                    email_selectors = ["a.email", ".email", "[itemprop='email']", "[data-tracking='email']"]
                    for selector in email_selectors:
                        try:
                            email_elem = listing.find_element(By.CSS_SELECTOR, selector)
                            email = email_elem.get_attribute("href")
                            if email and email.startswith("mailto:"):
                                email = email[7:]
                            if email:
                                break
                        except NoSuchElementException:
                            continue

                    data.append({
                        "Name": name,
                        "Address": address,
                        "Phone": phone,
                        "Website": website,
                        "Email": email
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

class StreetDirectoryScraper(WebsiteScraper):
    def __init__(self):
        super().__init__("https://www.streetdirectory.com/businessfinder/company_listing.php")

    def scrape_data(self, search_term, max_pages, headless_mode):
        # Implement scraping logic for StreetDirectory
        # This is a placeholder and should be implemented based on the website's structure
        return [], False

class TimesBusinessDirectoryScraper(WebsiteScraper):
    def __init__(self):
        super().__init__("https://www.timesbusinessdirectory.com/company-listings")

    def scrape_data(self, search_term, max_pages, headless_mode):
        # Implement scraping logic for TimesBusinessDirectory
        # This is a placeholder and should be implemented based on the website's structure
        return [], False

class WebScraperGUI:
    def __init__(self, master):
        self.master = master
        master.title("Web Scraper")

        self.scraping_active = False
        self.default_path = self.get_documents_path()
        self.scraper = None
        self.headless_mode = False

        self.frames = {}
        self.create_widgets()

        # Show the main screen directly
        self.show_frame('MainScreen')

    def create_widgets(self):
        self.create_menu()

        self.frames['MainScreen'] = ttk.Frame(self.master)

        self.create_main_screen()

    def create_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Set Default Path", command=self.set_default_path)
        file_menu.add_command(label="Open Default Path", command=self.open_default_path)
        file_menu.add_command(label="Headless Mode", command=self.toggle_headless_mode)
        file_menu.add_command(label="Stop Scraping", command=self.stop_scraping)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

    def create_main_screen(self):
        frame = self.frames['MainScreen']
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.website_label = ttk.Label(frame, text="Select Website:")
        self.website_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.website_combobox = ttk.Combobox(frame, values=["Yellow Pages", "Street Directory", "Times Business Directory"], state="readonly")
        self.website_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.website_combobox.current(0)  # Default to the first option
        self.website_combobox.bind("<<ComboboxSelected>>", self.update_scraper_class)

        self.search_label = ttk.Label(frame, text="Search Term:")
        self.search_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)

        self.search_entry = ttk.Entry(frame)
        self.search_entry.grid(row=1, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.search_entry.bind('<KeyRelease>', self.update_output_filename)

        self.max_pages_label = ttk.Label(frame, text="Maximum Pages:")
        self.max_pages_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)

        self.max_pages_entry = ttk.Entry(frame)
        self.max_pages_entry.grid(row=2, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.all_pages_var = tk.BooleanVar()
        self.all_pages_check = ttk.Checkbutton(frame, text="Scrape All Pages", variable=self.all_pages_var, command=self.toggle_max_pages)
        self.all_pages_check.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)

        self.output_file_label = ttk.Label(frame, text="Output File:")
        self.output_file_label.grid(row=4, column=0, padx=5, pady=5, sticky=tk.W)

        self.output_file_entry = ttk.Entry(frame)
        self.output_file_entry.grid(row=4, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))

        self.start_button = ttk.Button(frame, text="Start Scraping", command=self.start_scraping)
        self.start_button.grid(row=6, column=0, columnspan=2, padx=5, pady=10, sticky=(tk.W, tk.E))

        self.progress_label = ttk.Label(frame, text="")
        self.progress_label.grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))

    def update_scraper_class(self, event):
        website = self.website_combobox.get()
        if website == "Yellow Pages":
            self.scraper = YellowPagesScraper()
        elif website == "Street Directory":
            self.scraper = StreetDirectoryScraper()
        elif website == "Times Business Directory":
            self.scraper = TimesBusinessDirectoryScraper()

    def update_output_filename(self, event):
        search_term = self.search_entry.get().strip().replace(" ", "_")
        default_filename = f"{search_term}.csv" if search_term else "output.csv"
        self.output_file_entry.delete(0, tk.END)
        self.output_file_entry.insert(0, default_filename)

    def toggle_max_pages(self):
        if self.all_pages_var.get():
            self.max_pages_entry.configure(state="disabled")
        else:
            self.max_pages_entry.configure(state="normal")

    def set_default_path(self):
        self.default_path = filedialog.askdirectory(initialdir=self.default_path)
        messagebox.showinfo("Default Path", f"Default path set to:\n{self.default_path}")

    def open_default_path(self):
        if platform.system() == "Windows":
            os.startfile(self.default_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", self.default_path])
        else:
            subprocess.Popen(["xdg-open", self.default_path])

    def get_documents_path(self):
        if platform.system() == "Windows":
            return str(Path.home() / "Documents")
        elif platform.system() == "Darwin":
            return str(Path.home() / "Documents")
        else:
            return str(Path.home())

    def toggle_headless_mode(self):
        self.headless_mode = not self.headless_mode
        state = "enabled" if self.headless_mode else "disabled"
        messagebox.showinfo("Headless Mode", f"Headless mode is now {state}.")

    def start_scraping(self):
        if self.scraping_active:
            messagebox.showwarning("Warning", "Scraping is already in progress.")
            return

        if self.scraper is None:
            messagebox.showwarning("Warning", "Please select a website first.")
            return

        search_term = self.search_entry.get().strip()
        max_pages = self.max_pages_entry.get().strip()
        if not max_pages.isdigit():
            messagebox.showwarning("Warning", "Please enter a valid number of pages.")
            return

        max_pages = int(max_pages)
        output_file = self.output_file_entry.get().strip()

        if not output_file.endswith(".csv"):
            messagebox.showwarning("Warning", "Output file must be a .csv file.")
            return

        headless_mode = self.headless_mode

        self.scraping_active = True
        self.progress_label.config(text="Scraping in progress...")
        self.master.update_idletasks()

        try:
            data, max_page_reached = self.scraper.scrape_data(search_term, max_pages, headless_mode)
            df = pd.DataFrame(data)
            df.to_csv(os.path.join(self.default_path, output_file), index=False)
            messagebox.showinfo("Success", f"Scraping completed! Data saved to {output_file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            self.scraping_active = False
            self.progress_label.config(text="")

    def stop_scraping(self):
        if not self.scraping_active:
            messagebox.showinfo("Info", "No active scraping process to stop.")
            return
        self.scraping_active = False
        messagebox.showinfo("Stopped", "Scraping has been stopped.")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()

if __name__ == "__main__":
    root = tk.Tk()
    app = WebScraperGUI(root)
    root.mainloop()
