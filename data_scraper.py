from webdriver_manager.chrome import ChromeDriverManager

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import json

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
driver.get('https://results.eci.gov.in/PcResultGenJune2024/index.htm')

states = driver.find_elements(By.XPATH,"//select[@name='state']/option")
states_list = []
for p in range(1,len(states)):
    st = states[p]
    info = {
        "name" : st.text,
        "code" : st.get_attribute("value")
    }
    states_list.append(info)
    print(info)

district_list = []
for s in states_list:
    surl = "https://results.eci.gov.in/PcResultGenJune2024/partywiseresult-{}.htm".format(s['code'])
    driver.get(surl)
    districts = driver.find_elements(By.XPATH,"//select[@name='state']/option")
    for d in range(1,len(districts)):
        dt = districts[d]
        info = {
            "name" : dt.text.split('-')[0].strip(),
            "code" : dt.get_attribute("value"),
            "state" : s['name'],
            "scode" : s['code']
        }
        district_list.append(info)
        

print(len(district_list))
all_candidates_list = []
for d in district_list:
    durl = "https://results.eci.gov.in/PcResultGenJune2024/candidateswise-{}.htm".format(d['code'])
    driver.get(durl)
    candidates = driver.find_elements(By.XPATH,"//div[@class='cand-box']")
    for c in range(len(candidates)):
        cd = candidates[c]
        innerHtml = cd.get_attribute("innerHTML")
        # print(innerHtml)
        # Parse candidate information
        soup = BeautifulSoup(innerHtml, 'html.parser')
        img_tag = soup.find('img')
        url = img_tag['src']
        voteinfo_div = soup.find('div', class_='status')
        status_div = voteinfo_div.find('div')
        status = status_div.text
        vote_div = status_div.find_next_sibling('div')
        vote_val = vote_div.text
        # print(vote_val)
        if ('Uncontested'.lower() == vote_val.strip().lower()):
            vote_count = 'NA'
            vote_margin = 'NA'
        else:
            vote_count, vote_margin = vote_div.text.split('(')
            vote_margin = vote_margin.split(')')[0].strip('+ ')
        name = soup.find('h5').text
        party = soup.find('h6').text
        info = {
            "text" : cd.text,
            "url" : url,
            "status" : status,
            "votes" : vote_count,
            "margin" : vote_margin,
            "name" : name,
            "party" : party,
            "constituency_name" : d['name'],
            "constituency_code" : d['code'],
            "state_name" : d['state'],
            "state_code" : d['scode']
        }
        all_candidates_list.append(info)
        print(info)

driver.quit()

file_path = "database/candidate_data.json"
with open(file_path, "w") as json_file:
    json.dump(all_candidates_list, json_file, indent=4)

print(f"JSON data saved to {file_path}")

