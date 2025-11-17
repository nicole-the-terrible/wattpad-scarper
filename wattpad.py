#! /usr/bin/python3
import argparse
import bs4
import requests
import pyperclip
import re
import pypandoc
import os

base_apiV2_url = "https://www.wattpad.com/apiv2/"
base_apiV3_url = "https://www.wattpad.com/api/v3/"
dev_error_msg = "Please check the url again, for valid story id. Contact the developer if you think this is a bug."
url = "https://www.wattpad.com/story/374225710-calculus-of-the-heart"

def get_chapter_id(url):
    """Extracts the chapter ID from the given URL."""
    search_id = re.compile(r'\d{5,}')
    id_match = search_id.search(url)
    if id_match:
        return id_match.group()
    return None


def download_webpage(url):
    """Downloads the webpage content from the given URL."""
    try:
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        res.raise_for_status()
        return res.text
    except requests.exceptions.RequestException as exc:
        print("There was a problem: %s" % (exc))
        return None


def extract_useful_data(json_data):
    """Extracts useful data from the JSON response."""
    description = json_data.get('description', '')
    tags = json_data.get('tags', '')
    chapters = json_data.get('parts', '')
    title = json_data.get('title', '')
    author = json_data.get('user', '')
    cover = json_data.get('cover', '')
    return description, tags, chapters, title, author, cover


def save_html_file(file_name, story_title, author, cover, tags, description, chapters):
    """Saves the HTML file with the given data."""
    file = open(file_name, 'w', encoding='utf-8')

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
        <div align="center">{description}</div>
        
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
        print(f"Getting Chapter {i + 1}....")
        chapter_url = base_apiV2_url + f"storytext?id={chapter['id']}"
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
    print(f"Saved {file_name}")


def save_epub_file(html_file, story_title, cover):
    """Converts the HTML file to EPUB format and saves it."""
    print("Generating EPUB...")
    story_title = story_title.replace('/', ' ')
    cover_image = f"{story_title}.jpg"
    res_img = requests.get(cover, headers={'User-Agent': 'Mozilla/5.0'})
    open(cover_image, 'wb').write(res_img.content)
    output_file = f"{story_title}.epub"

    pypandoc.convert_file(html_file, 'epub3', outputfile=output_file, extra_args=['--epub-chapter-level=2', f'--epub-cover-image={cover_image}'], sandbox=False)

    os.remove(cover_image)
    print(f"Saved {output_file}")


def main(url):
    story_id = get_chapter_id(url)
    if not story_id:
        print(dev_error_msg)
        return

    # Getting JSON data from Wattpad API.
    story_info_url = base_apiV3_url + f"stories/{story_id}?drafts=0&mature=1&include_deleted=1&fields=id,title,createDate,modifyDate,description,url,firstPublishedPart,cover,language,user(name,username,avatar,location,numStoriesPublished,numFollowing,numFollowers,twitter),completed,numParts,lastPublishedPart,parts(id,title,length,url,deleted,draft,createDate),tags,storyLanguage,copyright"
    json_data  = requests.get(story_info_url, headers={'User-Agent': 'Mozilla/5.0'}).json()
    try:
        if json_data.get('result') == 'ERROR':
            error_message = json_data.get('message', 'Unknown error')
            print(f"Error: {error_message}")
            print(dev_error_msg)
            return
        
        if json_data.get('error_type') :
            error_message = json_data.get('message', 'Unknown error')
            print(f"Error: {error_message}")
            print(dev_error_msg)
            return
        
    
        if json_data.get('result') == 'ERROR':
            error_message = json_data.get('message', 'Unknown error')
            print(f"API Error: {error_message}")
            return
    except Exception as exc:
        print(f"Error retrieving JSON data from the API: {exc}")
        return

    # Extracting useful data from JSON.
    description, tags, chapters, story_title, author, cover = extract_useful_data(json_data)

    # Saving HTML file.
    html_file_name = f"{story_title}.html"
    html_file_name = html_file_name.replace('/', ' ')
    save_html_file(html_file_name, story_title, author, cover, tags, description, chapters)

    # Converting HTML to EPUB.
    save_epub_file(html_file_name, story_title, cover)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Wattpad2epub: Convert Wattpad stories to EPUB format.')
    parser.add_argument('url', nargs='?', help='URL of the Wattpad Story')
    args = parser.parse_args()

    if args.url:
        main(args.url)
    else:
        # Getting address from clipboard.
        url = pyperclip.paste()
        main(url)