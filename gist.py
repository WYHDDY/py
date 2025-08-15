import requests
from lxml import html
import time
from urllib.parse import quote_plus

PROXIES = None

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'zh;q=0.9,en;q=0.8',
    'Connection': 'keep-alive',
}


def fetch_page_content(url, session):
    try:
        response = session.get(url, headers=HEADERS, proxies=PROXIES, timeout=20)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {url} - {e}")
        return None

def run_scraper(search_terms):
    print("--- 启动 Gist 爬虫模式 ---")
    
    start_page = 1
    end_page = 3
    print(f"ℹ️ 已固定爬取页数范围为: {start_page} 到 {end_page}")

    print("ℹ️ 未设置代理，将直接连接。")

    all_final_urls = []

    with requests.Session() as session:
        for search_query in search_terms:
            print(f"\n--- 开始搜索内容: '{search_query}' ---")
            encoded_query = quote_plus(search_query)

            for page_num in range(start_page, end_page + 1):
                search_url = f"https://gist.github.com/search?l=YAML&o=desc&p={page_num}&q={encoded_query}&s=updated"
                print(f"\n📄 正在处理第 {page_num} 页: {search_url}")

                html_content = fetch_page_content(search_url, session)
                if not html_content:
                    continue

                tree = html.fromstring(html_content)
                gist_snippets = tree.xpath("//div[@class='gist-snippet']")

                if not gist_snippets:
                    print(f"    -> 在第 {page_num} 页未找到任何 Gist 结果。")
                    break
                
                print(f"    -> 在第 {page_num} 页找到 {len(gist_snippets)} 个 Gist 结果。")

                for index, snippet in enumerate(gist_snippets):
                    partial_links = snippet.xpath(".//div[contains(@class, 'gist-snippet-meta')]//a[1]")
                    
                    if not partial_links: continue
                    partial_gist_href = partial_links[0].get('href')
                    if not partial_gist_href: continue

                    full_gist_url = f"https://gist.github.com{partial_gist_href}"
                    
                    print(f"      [{index + 1}/{len(gist_snippets)}] 正在访问 Gist 页面: {full_gist_url}")
                    gist_page_content = fetch_page_content(full_gist_url, session)
                    if not gist_page_content: continue

                    gist_tree = html.fromstring(gist_page_content)
                    raw_link_elements = gist_tree.xpath("//a[contains(., 'Raw')]")

                    if raw_link_elements:
                        raw_file_href = raw_link_elements[0].get('href')
                        final_url = f"https://gist.github.com{raw_file_href}"
                        
                        if final_url.endswith('all.yaml'):
                            print(f"      ✅ 成功提取: {final_url}")
                            all_final_urls.append(final_url)
                        else:
                            print(f"      ➡️ 链接不符合要求，已跳过: {final_url}")
                    else:
                        print(f"      ⚠️ 在 Gist 页面 {full_gist_url} 未找到 'Raw' 链接。")
                    
                    time.sleep(0.5)

    if all_final_urls:
        unique_urls = sorted(list(set(all_final_urls)))
        count = len(unique_urls)
        filename = "gist.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            for url in unique_urls:
                f.write(f"{url}\n")
        
        print(f"\n🎉 任务完成! 共提取 {count} 个去重后的 URL，已保存到文件: {filename}")
    else:
        print("\n🤷‍ 任务结束，没有提取到任何 URL。")

# --- 主程序入口 ---
if __name__ == "__main__":
    fixed_search_terms = ['ss', 'ssr', 'vless', 'vmess', 'trojan']
    run_scraper(fixed_search_terms)
