from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ChromeOptions
import requests
import time
import os
import random
import hashlib
from proxies import proxies, user_agents
import concurrent.futures
import json
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from PIL import Image
import io
import imagehash

WORKING_PROXIES_CACHE = set()
PROXY_TIMEOUT = 3

def verify_proxy(proxy):
    try:
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'DNT': '1'
        }
        proxies = {
            'http': f'http://{proxy}',
            'https': f'http://{proxy}'
        }
        # Test multiple URLs to ensure proxy works
        test_urls = [
            'https://www.bing.com',
            'https://www.yahoo.com',
            'https://duckduckgo.com'
        ]
        for url in test_urls:
            response = requests.get(url, proxies=proxies, headers=headers, timeout=5)
            if response.status_code != 200:
                return False
        return True
    except:
        return False

def get_random_proxies(n=5):
    return random.sample(proxies, min(n, len(proxies)))

def get_working_proxy():
    if WORKING_PROXIES_CACHE:
        proxy = random.choice(list(WORKING_PROXIES_CACHE))
        print(f"Using cached proxy: {proxy}")
        return proxy
    
    print("Testing random proxies...")
    tested_proxies = set()
    max_attempts = 10
    
    while len(tested_proxies) < len(proxies) and max_attempts > 0:
        # Get 5 random untested proxies
        candidates = [p for p in get_random_proxies() if p not in tested_proxies]
        if not candidates:
            break
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_proxy = {executor.submit(verify_proxy, proxy): proxy for proxy in candidates}
            
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                tested_proxies.add(proxy)
                try:
                    if future.result():
                        executor.shutdown(wait=False)
                        WORKING_PROXIES_CACHE.add(proxy)
                        print(f"Found working proxy: {proxy}")
                        return proxy
                except:
                    continue
        
        max_attempts -= 1
    
    print("No working proxies found, trying without proxy")
    return None

def setup_driver(use_proxy=True):
    options = ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-automation')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    if use_proxy:
        proxy = get_working_proxy()
        if proxy:
            options.add_argument(f'--proxy-server=http://{proxy}')
            print(f"Using proxy: {proxy}")
    
    # Add random user agent and other headers
    options.add_argument(f'--user-agent={random.choice(user_agents)}')
    
    service = Service('./chromedriver')
    try:
        driver = webdriver.Chrome(service=service, options=options)
        # Remove webdriver flags
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(user_agents)
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"Failed to create driver: {e}")
        return None

def get_image_fingerprint(image_data):
    try:
        img = Image.open(io.BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return str(imagehash.average_hash(img))
    except:
        return hashlib.md5(image_data).hexdigest()

def clean_duplicates(save_path, class_name):
    print("Cleaning existing duplicates...")
    images_dir = os.path.join(save_path, class_name)
    if not os.path.exists(images_dir):
        return set()
    
    hashes = {}
    duplicates = []
    unique_hashes = set()
    
    for file in os.listdir(images_dir):
        if file.endswith(('.jpg', '.jpeg', '.png')):
            file_path = os.path.join(images_dir, file)
            try:
                with Image.open(file_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img_hash = str(imagehash.average_hash(img))
                    
                    if img_hash in hashes:
                        duplicates.append(file_path)
                    else:
                        hashes[img_hash] = file_path
                        unique_hashes.add(img_hash)
            except Exception as e:
                print(f"Error processing {file}: {e}")
    
    for duplicate in duplicates:
        try:
            os.remove(duplicate)
            print(f"Removed duplicate: {os.path.basename(duplicate)}")
        except Exception as e:
            print(f"Error removing {duplicate}: {e}")
    
    print(f"Removed {len(duplicates)} duplicates, {len(unique_hashes)} unique images remain")
    return unique_hashes

def load_more_images(driver, min_thumbnails=150):
    thumbnails = []
    scroll_count = 0
    max_scrolls = 30  
    
    while len(thumbnails) < min_thumbnails and scroll_count < max_scrolls:
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        
        # Try to click "Show more results" if available
        try:
            show_more = driver.find_element(By.CSS_SELECTOR, "input[type='button'][value='Show more results']")
            driver.execute_script("arguments[0].click();", show_more)
            time.sleep(2)
            print("Clicked 'Show more results'")
        except:
            pass
        
        # Get current thumbnails
        thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.tile--img__img")
        print(f"Found {len(thumbnails)} thumbnails after scroll {scroll_count + 1}")
        scroll_count += 1
        
    return len(thumbnails)

def download_image(url, save_path, index, existing_hashes, query):
    try:
        headers = {'User-Agent': random.choice(user_agents)}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            image_data = response.content
            
            try:
                img = Image.open(io.BytesIO(image_data))
                if img.mode != 'RGB':
                    print(f"\n⚠️ Skipping non-RGB image (Mode: {img.mode})")
                    return None, False
                
                img = img.convert('RGB')
                
                # Get hash after ensuring RGB
                img_hash = get_image_fingerprint(image_data)
                
                if img_hash not in existing_hashes:
                    img_name = f"{query.replace(' ', '_')}_{index}_{random.randint(1000, 9999)}.jpg"
                    img_path = os.path.join(save_path, img_name)
                    
                    # Save the RGB image
                    img.save(img_path, 'JPEG')
                    return img_hash, True
            except Exception as e:
                print(f"\n❌ Error processing image: {e}")
                return None, False
                
    except Exception as e:
        print(f"Error downloading image: {e}")
    return None, False

def get_full_res_image(driver, thumbnail):
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", thumbnail)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", thumbnail)
        time.sleep(2)

        full_res = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".detail__media__img-highres"))
        )
        return full_res.get_attribute("src")
    except:
        return None

def scrape_images(query, num_images, save_path, class_name, max_retries=3):
    existing_hashes = clean_duplicates(save_path, class_name)
    current_count = len(existing_hashes)
    images_dir = os.path.join(save_path, class_name)
    os.makedirs(images_dir, exist_ok=True) 
    
    print(f"Currently have {current_count} images, continuing download...")
    print(f"Saving images to: {images_dir}")
    
    stats = {
        'processed': 0,
        'skipped_duplicates': 0,
        'failed_downloads': 0,
        'successful_downloads': 0,
        'consecutive_skips': 0
    }
    
    for attempt in range(max_retries):
        driver = setup_driver(use_proxy=(attempt > 0))
        if not driver:
            continue
            
        try:
            search_url = f"https://duckduckgo.com/?q={query}&iax=images&ia=images"
            driver.get(search_url)
            time.sleep(2)
            
            consecutive_skips = 0
            min_thumbnails = 200
            
            while current_count < num_images:
                num_thumbnails = load_more_images(driver, min_thumbnails)
                print(f"\nLoaded batch of {num_thumbnails} thumbnails")
                
                thumbnails = driver.find_elements(By.CSS_SELECTOR, "img.tile--img__img")
                
                for i, thumbnail in enumerate(thumbnails):
                    try:
                        if consecutive_skips >= 10:
                            print("\nDetected 10 consecutive skips. Scrolling to load fresh content...")
                            
                            for _ in range(5):
                                driver.execute_script(
                                    "window.scrollTo(0, window.scrollY + window.innerHeight * 2);"
                                )
                                time.sleep(1)
                            consecutive_skips = 0
                            break  
                        
                        stats['processed'] += 1
                        print(f"\rProcessing thumbnail {i+1}/{len(thumbnails)}", end="")
                        
                        img_url = get_full_res_image(driver, thumbnail)
                        if not img_url:
                            stats['failed_downloads'] += 1
                            print(f"\n❌ Failed to get URL for thumbnail {i+1}")
                            continue
                            
                        # Download and process image
                        headers = {'User-Agent': random.choice(user_agents)}
                        response = requests.get(img_url, stream=True, timeout=10)
                        
                        if response.status_code == 200:
                            image_data = response.content
                            img_hash = get_image_fingerprint(image_data)
                            
                            if img_hash not in existing_hashes:
                                img_name = f"{class_name}_{current_count+1:04d}_{random.randint(1,999):03d}.jpg"
                                img_path = os.path.join(images_dir, img_name)
                                
                                with open(img_path, 'wb') as file:
                                    file.write(image_data)
                                
                                existing_hashes.add(img_hash)
                                current_count += 1
                                stats['successful_downloads'] += 1
                                stats['consecutive_skips'] = 0  
                                print(f"\n✅ Downloaded new image {current_count}/{num_images}")
                            else:
                                stats['skipped_duplicates'] += 1
                                stats['consecutive_skips'] += 1
                                print(f"\n⏭️  Skipped duplicate image")
                                print(f"\nConsecutive skips: {stats['consecutive_skips']}/20")
                                
                                if stats['consecutive_skips'] >= 20:
                                    print("\nReached skip limit, moving to next query...")
                                    return current_count
                                
                           
                            try:
                                close_button = driver.find_element(By.CSS_SELECTOR, "button.module__close")
                                close_button.click()
                                time.sleep(0.5)
                            except:
                                pass
                            
                            if current_count >= num_images:
                                break
                                
                    except Exception as e:
                        stats['failed_downloads'] += 1
                        print(f"\n❌ Error: {str(e)[:100]}")
                        continue
                
                print(f"\nBatch Summary:")
                print(f"Processed: {stats['processed']}")
                print(f"Downloads: {stats['successful_downloads']}")
                print(f"Skipped: {stats['skipped_duplicates']}")
                print(f"Failed: {stats['failed_downloads']}")
                
                if current_count >= num_images:
                    break
                
               
                if stats['skipped_duplicates'] > 20:
                    print("\nToo many skipped images, moving to next batch...")
                    break
                    
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            continue
        finally:
            if driver:
                driver.quit()
        
        if current_count >= num_images:
            break

    return current_count

if __name__ == "__main__":
    save_path = "dataset/raw"
    batch_terms = {
#         "Holstein":[
#             "my beautifull Holstein cow HD",
# "Holstein cow HD",
#     "Holstein cow  grazing in open field",
#     "Close-up of Holstein cow face",
#     "Black and white Holstein cow standing",
#     "Holstein cow in dairy farm setting",
#     "Full body Holstein cow portrait",
#     "Holstein cow with calf",
#     "Holstein cow in sunny meadow",
#     "Holstein cow side view",
#     "Holstein cow in winter",
#     "High-resolution Holstein cow image"
# ]

# "Hereford":[
#      "my beautifull Hereford cow HD",
#    "Red Hereford cow with white face grazing",
# "Close-up of Hereford cow muzzle",
# "Hereford cow in pasture",
# "Hereford cow full body shot",
# "Hereford cow in ranch setting",
# "Hereford cow standing in field",
# "Hereford cow with calf",
# "Hereford cow in sunny day",
# "Hereford cow side profile",
# "High-resolution Hereford cow image",
# ]

 "Angus": [
    "my beautifull Angus cow HD",
    "Solid black Angus cow grazing hd",
    "Close-up of Angus cow face",
    "Angus cow in field",
    "Full body Angus cow portrait",
    "Angus cow in beef farm",
    "Angus cow standing in grassland",
    "Angus cow with calf",
    "Angus cow in summer",
    "Angus cow side view",
    "High-resolution Angus cow image",
        ]

      
    }



     
    
    total_images_needed = 1000
    images_per_term = total_images_needed // len(batch_terms["Angus"])
    remaining_images = total_images_needed % len(batch_terms["Angus"])
    
    print(f"Will download approximately {images_per_term} images per search term")
    
    for class_name, terms in batch_terms.items():
        current_total = 0
        
        for term in terms:
            print(f"\nSearching for: {term}")
            
            try:
                images_downloaded = scrape_images(term, num_images=1000, save_path=save_path, class_name=class_name)
                current_total += images_downloaded
                print(f"Total images so far: {current_total}")
                
                # Add delay between terms
                time.sleep(random.uniform(5, 10))
                
            except Exception as e:
                print(f"Error scraping {term}: {e}")
                continue
            
        print(f"\nFinished with {current_total} total images")


        


      


# "Hereford":[
#     ""
#    "Red Hereford cow with white face grazing",
# "Close-up of Hereford cow muzzle",
# "Hereford cow in pasture",
# "Hereford cow full body shot",
# "Hereford cow in ranch setting",
# "Hereford cow standing in field",
# "Hereford cow with calf",
# "Hereford cow in sunny day",
# "Hereford cow side profile",
# "High-resolution Hereford cow image",
# ]


#  "Holstein":[
#"Holstein cow HD",
#     "Holstein cow  grazing in open field",
#     "Close-up of Holstein cow face",
#     "Black and white Holstein cow standing",
#     "Holstein cow in dairy farm setting",
#     "Full body Holstein cow portrait",
#     "Holstein cow with calf",
#     "Holstein cow in sunny meadow",
#     "Holstein cow side view",
#     "Holstein cow in winter",
#     "High-resolution Holstein cow image"
# ]




#  "Angus": [
#     "Solid black Angus cow grazing hd",
#     "Close-up of Angus cow face",
#     "Angus cow in field",
#     "Full body Angus cow portrait",
#     "Angus cow in beef farm",
#     "Angus cow standing in grassland",
#     "Angus cow with calf",
#     "Angus cow in summer",
#     "Angus cow side view",
#     "High-resolution Angus cow image",
#         ]