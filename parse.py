from bs4 import BeautifulSoup

innerHtml1 = """<figure><img src="https://results.eci.gov.in/uploads4/candprofile/2024/PC/E24/U01/BISHN-2024-169.jpg" alt=""></figure>
                    <div class="cand-info">
                        <div class="status won">
                                                     <div style="text-transform: capitalize">won</div>
                            <div>102436 <span>(+ 24396)</span></div>
                                                    </div>
                        <div class="nme-prty">
                            <h5>BISHNU PADA RAY</h5>
                            <h6>Bharatiya Janata Party</h6>
                        </div>
                    </div>"""

innerHtml2 = """ <figure><img src="https://results.eci.gov.in/uploads4/candprofile/2024/PC/E24/S06/MUKES-2024-4763.jpg" alt=""></figure>
                    <div class="cand-info">
                        <div class="status won">
                                              <div style="text-transform: capitalize">won</div>
                            <div>Uncontested </div>
                                                    </div>
                        <div class="nme-prty">
                            <h5>MUKESHKUMAR CHANDRAKAANT DALAL</h5>
                            <h6>Bharatiya Janata Party</h6>
                        </div>
                    </div>"""
#print(innerHtml)
# Parse candidate information
soup = BeautifulSoup(innerHtml1, 'html.parser')
print(soup.prettify())
img_tag = soup.find('img')
url = img_tag['src']
voteinfo_div = soup.find('div', class_='status')
status_div = voteinfo_div.find('div')
print(status_div)
status = status_div.text
print(status)
vote_div = status_div.find_next_sibling('div')
vote_val = vote_div.text
print(vote_val)
if ('Uncontested'.lower() == vote_val.strip().lower()):
    vote_count = 'NA'
    vote_margin = 'NA'
else:
    vote_count, vote_margin = vote_div.text.split('(')
    vote_margin = vote_margin.strip('+ ')

print(vote_count)
vote_margin = vote_margin.split(')')[0]
name = soup.find('h5').text
party = soup.find('h6').text
info = {
    "url" : url,
    "status" : status,
    "votes" : vote_count,
    "margin" : vote_margin,
    "comment" : vote_val,
    "name" : name,
    "party" : party
}

print(info)
