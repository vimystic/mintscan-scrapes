import sys
import time
from playwright.sync_api import sync_playwright

def click_next_button(page, next_button_selector):
    try:
        next_button = page.query_selector(next_button_selector)
        if next_button:
            next_button.click()
            page.wait_for_timeout(5000)  # wait for 5 seconds before processing next page
            return True
        else:
            print("Next button not found or disabled. Ending pagination.")
            return False
    except Exception as e:
        print(f"Failed to click the next button normally: {e}")
        return False

def click_next_button_alternative(page, next_button_selector):
    try:
        next_button = page.query_selector(next_button_selector)
        if next_button:
            # Scroll the button into view
            page.evaluate('''(selector) => {
                const element = document.querySelector(selector);
                if (element) {
                    element.scrollIntoView({ behavior: "smooth", block: "center" });
                }
            }''', next_button_selector)
            
            # Use bounding box coordinates to click
            box = next_button.bounding_box()
            page.mouse.click(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
            
            page.wait_for_timeout(5000)  # wait for 5 seconds before processing next page
            return True
        else:
            print("Next button not found or disabled. Ending pagination.")
            return False
    except Exception as e:
        print(f"Failed to click the next button using alternative method: {e}")
        return False

def run(playwright, base_url, filename):
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    
    # Open the file for writing
    with open(filename, "a") as file:
        file.write("TxHash,Block,Fee,Token,Date,Time" + "\n")
        
        page.goto(base_url)
        
        # Wait for Transactions section to load
        page.wait_for_selector("text=Transactions", timeout=60000)
        
        page_num = 1
        while True:
            # Wait for transaction items to load
            page.wait_for_selector(".item-container", timeout=60000)
            
            tx_containers = page.query_selector_all(".item-container")
            if len(tx_containers) >= 10:
                for container in tx_containers:
                    op = container.inner_text().replace("\n+", "").replace("(", "\n(").replace(",", "")
                    lines = [line for index, line in enumerate(op.split("\n")) if index not in [1, 2, 4, 9]]
                    op = ",".join(lines).replace(" ,", ",")
                    op = op[::-1].replace(",", " ", 1)[::-1].replace("st", "").replace("th", "").replace("rd", "").replace("nd", "")
                    file.write(op + "\n")
            else:
                print(f"Found only {len(tx_containers)} transaction items, waiting for more to load...")
                time.sleep(5)  # wait for 5 seconds before checking again
                continue
            
            next_button_selector = 'div.pagination-button:not([data-disable]) svg path[d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z"]'
            
            if not click_next_button(page, next_button_selector):
                if not click_next_button_alternative(page, next_button_selector):
                    break  # Exit the loop if both click methods fail
            
            page_num += 1
        
        print("Finished processing all pages.")
    
    browser.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <base_url> <filename>") #baseurl will be a mintscan url. like https://www.mintscan.io/osmosis/address/osmo1ugku28hwyexpljrrmtet05nd6kjlrvr9jz6z00
        sys.exit(1)
    
    base_url = sys.argv[1]
    filename = sys.argv[2]
    
    with sync_playwright() as playwright:
        run(playwright, base_url, filename)
