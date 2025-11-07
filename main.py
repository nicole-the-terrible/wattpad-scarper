"""
#typing with nails extension on is sooooo annoying 
"""

import os
import requests
import bs4 
import pypandoc
import re
import argparse
import pyperclip

apiV2_url = "https://www.wattpad.com/apiv2/"
api_V3_url = "https://www.wattpad.com/apiv3/"
error_msg = "ERROR:check the url, for valid id"

def get_chap_id(url):
    search_id = re.compile(r'\d{5,}')
    id_match = search_id.search(url)
    if id_match:
        return id_match.group()
    return None

def download_webpage(url):
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        res.raise_for_status()
        return res.text
    except requests.exceptions.RequestException as esx:
        print("There was a problem: %s % (exc)")
        return None

def extract_data(json):
    description = json.get('description', '')
    title = json.get('title', '')
    author = json.get('user', '')
    cover = json.get('cover', '')
    tags = json.get('tags', '')
    chapters = json.get('part', '')
    
    
    return title, author, cover, tags, chapters, description

def save_html(file_name, story_title, author, cover, tags, chapters, description):
    file = open (file_name, 'w', encoding='utf-8')
    
    file.write(f"""
        <html>
        <head>
            <meta name='title' content='{story_title}'>
            <meta name='author' content='{author["name"]}' >
        </head>
        <body>
        <div style="text-align:center;">
            <img src="{cover}" alt="cover_image">
        </div>
        <br>
        <h5 align="center">{story_title}</h5>
        <h6 align="center">By {author["name"]} : <a href="https://www.wattpad.com/user/{author["username"]}">{author["username"]}</a></h6>

        <div align="center">Tags: {tags} </div>
        <br><br>
        <div alight ="center">{description}<div>
        <br><br>
        <div align="left">
            <h6>
                * If chapter number or names are jumbled up, it's definitely the author's fault.
                (Author-san, please number them correctly and in order.)<br>
                * Converted using Wattpad2epub by Architrixs<br>
            </h6>
        </div>
    """)
    for i, chapter in enumerate(chapters):
        print(f"getting chapter {i + 1}....")
        chapter_url = apiV2_url + f"storytext?id={chapter['id']}"
        chapter_content = download_webpage(chapter_url)
        if chapter_content:
            soup_res = bs4.BeautifulSoup(chapter_content, 'html.parser')
            file.write(f"""
                <br><br>
                <h2>Chapter {i + 1}: '{chapter['title']}'</h2><br><br>
                {soup_res.prettify()}
                """)
            file.write("</body></html>")
            file.close()
            print(f"saved {file_name}")

def save_epub_file(html_file, story_title, cover):
    print("saving EPUB...")
    story_title = story_title.replace('/', ' ')
    cover_image = f"{story_title}.jpg"
    res_img = requests.get(cover, headers={'User-Agent': 'Mozilla/5.0'})
    open(cover_image, 'wb').write(res_img.content)
    output_file = f"{story_title}.epub"

    pypandoc.convert_file(html_file, 'epub3', outputfile=output_file, extra_args=['--epub-chapter-level=2', f'--epub-cover-image={cover_image}'], sandbox=False)

    os.remove(cover_image)
    print(f"Saved {output_file}")