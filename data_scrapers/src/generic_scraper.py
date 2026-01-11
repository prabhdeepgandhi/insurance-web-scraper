from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
import json,re
from models import ScrapeResult, Insured, Agency, Policy
from playwright.sync_api import sync_playwright



class GenericScraper():

    def fetch(self, url: str) -> str:
        """
        Using Playwright to fetch content so it can wait for dynamic js content to load before scraping 
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle")
                content = page.content()
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                content = ""
            finally:
                browser.close()
        return content

    def parse(self, html_content: str) -> ScrapeResult:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. Raw Extraction
        raw_data = self._extract_generic_data(soup)
        # print(f"Raw data: {raw_data}")

        # 2. Mapping tp a Data Model so its generic irrepective page has table or list objects
        result = self._map_to_models(raw_data)
        result.raw_data = raw_data
                
        return result

    def scrape(self, start_url: str) -> ScrapeResult:
        """
        Scrape a url and see if there are multiple pages to scrape then scrape them all and merge the results
        """
        all_results = ScrapeResult()
        visited_urls = set()
        queue = [start_url]
        #bfs for looking for next page in case of pagination. bfs to go breadth first and manage repetition of urls if it comes up
        while queue:
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            try:
                html = self.fetch(current_url)
                if not html: 
                    print(f"Failed to fetch {current_url}")
                    continue
                
                result = self.parse(html)
                all_results.merge(result)
                
                soup = BeautifulSoup(html, 'html.parser')
                next_link = self._find_next_page(soup, current_url)
                if next_link and next_link not in visited_urls:
                    print(f"Found next page: {next_link}")
                    queue.append(next_link)
                    
            except Exception as e:
                print(f"Error scraping {current_url}: {e}")
                
        return all_results

    def _find_next_page(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        checking if there is pagination or a next page, using standard patterns but can also be custom numbers for pages
        """
        candidates = soup.find_all('a', href=True)
        for a in candidates:
            text = a.get_text(strip=True).lower()
            if text in ['next', 'next >', '>', 'next page', 'more']:
                try:
                    from urllib.parse import urljoin
                    return urljoin(current_url, a['href'])
                except:
                    pass
        return None

    def _extract_generic_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extracts data organized by sections.
        """
        data = {}
        

        current_section = "General"
        data[current_section] = {"tables": [], "kv_pairs": {}, "lists": []}
        
        all_elements = soup.find_all(recursive=True)
        # print(f"All elements: {all_elements}")
        
        
        headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        if not headers:
            data["General"] = self._extract_section_content(soup)
            return data

        first_header = headers[0]
        
        for i, header in enumerate(headers):
            section_name = header.get_text(strip=True)
            
            nodes = []
            curr = header.next_sibling
            while curr:
                if curr.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    break
                nodes.append(curr)
                curr = curr.next_sibling
            
            section_content = self._extract_from_nodes(nodes)
            
            if section_name in data:
                data[section_name]["tables"].extend(section_content["tables"])
                data[section_name]["lists"].extend(section_content["lists"])
                data[section_name]["kv_pairs"].update(section_content["kv_pairs"])
            else:
                data[section_name] = section_content
                
        return data

    def _extract_section_content(self, container) -> Dict:
        """Helper when we have a full section"""
        return {
            "tables": self._extract_tables(container),
            "lists": self._extract_lists(container),
            "kv_pairs": self._extract_key_values(container)
        }

    def _extract_from_nodes(self, nodes: List) -> Dict:
        """Helper when we have a list of sibling nodes"""
        
        tables = []
        lists = []
        kv_pairs = {}
        
        for node in nodes:
            if isinstance(node, str):
                continue 
            if not getattr(node, 'name', None):
                continue

            # Tables
            extracted_tables = self._extract_tables(node)
            tables.extend(extracted_tables)
            
            # Lists
            extracted_lists = self._extract_lists(node)
            lists.extend(extracted_lists)
            
            # Key-Values
            extracted_kvs = self._extract_key_values(node)
            kv_pairs.update(extracted_kvs)
            
        return {
            "tables": tables,
            "lists": lists,
            "kv_pairs": kv_pairs
        }

    def _extract_tables(self, node) -> List[Dict]:
        """ 
        Finds tables within a node and converts them to list-of-dicts.
        """
        found = []
        if node.name == 'table':
            candidates = [node]
        else:
            candidates = node.find_all('table')
            
        for table in candidates:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            rows = table.find_all('tr')
            
            table_data = []
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if all(c.name == 'th' for c in cells):
                    continue
                    
                row_dict = {}
                values = [c.get_text(strip=True) for c in cells]
                
                if len(headers) == len(values):
                    for h, v in zip(headers, values):
                        row_dict[h] = v
                else:
                    row_dict["values"] = values
                
                if row_dict:
                    table_data.append(row_dict)
            
            if table_data:
                found.append({"type": "table", "data": table_data})
                
        return found

    def _extract_lists(self, node) -> List[List[str]]:
        found = []
        if node.name in ['ul', 'ol']:
            candidates = [node]
        else:
            candidates = node.find_all(['ul', 'ol'])
            
        for l in candidates:
            list_data = []
            for li in l.find_all('li', recursive=False):
                local_kvs = self._extract_key_values(li)
                if local_kvs:
                    list_data.append(local_kvs)
                else:
                    text = li.get_text(strip=True)
                    parsed_kv = self._parse_mashed_string(text)
                    if len(parsed_kv) > 1:
                         list_data.append(parsed_kv)
                    else:
                        list_data.append(text)

            if list_data:
                found.append(list_data)
        return found

    def _parse_mashed_string(self, text: str) -> Dict[str, str]:
        """
        If there are details which are in labeled format,  i.e. everything in raw text coming together we need to parse it into key-value pairs.
        """
        pattern = re.compile(r'([A-Za-z\s]+):')
        
        matches = list(pattern.finditer(text))
        if not matches:
            return {}
            
        result = {}
        for i, match in enumerate(matches):
            key = match.group(1).strip()
            start_val = match.end()
            
            if i + 1 < len(matches):
                end_val = matches[i+1].start()
            else:
                end_val = len(text)
                
            val = text[start_val:end_val].strip()
            result[key] = val
        return result

    def _extract_key_values(self, node) -> Dict[str, str]:
        """
        convert to key value pair from dt or lables or divs
        """
        data = {}
        

        dls = [node] if node.name == 'dl' else node.find_all('dl')
        for dl in dls:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            for dt, dd in zip(dts, dds):
                key = dt.get_text(strip=True).rstrip(':')
                val = dd.get_text(strip=True)
                data[key] = val
                
        potential_keys = node.find_all(['b', 'strong', 'label', 'span', 'div'])
        for pk in potential_keys:

            if len(pk.get_text()) > 50: 
                continue

            text = pk.get_text(strip=True)
            if text.endswith(':'):
                key = text.rstrip(':')
                

                next_sib = pk.next_sibling
                val = None
                

                while next_sib and (isinstance(next_sib, str) and not next_sib.strip()):
                    next_sib = next_sib.next_sibling 

                if isinstance(next_sib, str) and next_sib.strip():
                   val = next_sib.strip()
                elif next_sib and getattr(next_sib, 'name', None):
                    val = next_sib.get_text(strip=True)
                    
                if val:
                    data[key] = val
                    
        return data

    def _map_to_models(self, raw_data: Dict[str, Any]) -> ScrapeResult:
        """
        Mapping raw extracted data to structured Data models (Insured, Agency, Policy).
        """

        result = ScrapeResult()
        
        all_kvs = self._flatten_key_values(raw_data)
        
        result.insured = self._extract_insured(all_kvs)
        result.agency = self._extract_agency(all_kvs)
        
        self._find_policies(raw_data, result)
        
        return result

    def _flatten_key_values(self, raw_data: Dict[str, Any]) -> Dict[str, str]:
        """
        movig all keys to use lowercase for easy mapping
        """
        all_kvs_normalized = {}
        for section in raw_data.values():
        
            for k, v in section.get('kv_pairs', {}).items():
                all_kvs_normalized[k.lower()] = v
            
        
            for item in section.get('lists', []):
        
                if isinstance(item, dict):
                     for k, v in item.items():
                         all_kvs_normalized[k.lower()] = v
                
                elif isinstance(item, list):
                     for sub in item:
                         if isinstance(sub, dict):
                             for k, v in sub.items():
                                 all_kvs_normalized[k.lower()] = v
        return all_kvs_normalized

    def _extract_insured(self, all_kvs: Dict[str, str]) -> Insured:
        """
        forming data as per Insured model for consistency
        """
        insured = Insured()
        mapping = {
            "insured name": "name", 
            "business name": "name",
            "customer name": "name", 
            "name": "name", 
            "address": "address",
            "insured address": "address",
            "age": "age",
            "email": "email",
        }
        
        for key, value in all_kvs.items():
            for pattern, attr in mapping.items():
                if getattr(insured, attr) is None and pattern in key:
                     if key == pattern:
                         if attr == 'age':
                             try: value = int(value)
                             except: continue
                         setattr(insured, attr, value)
        return insured

    def _extract_agency(self, all_kvs: Dict[str, str]) -> Agency:
        """
        forming data as per Agency model for consistency
        """

        agency = Agency()
        mapping = {
            "agency name": "name",
            "agent": "name",
            "broker": "name",
            "agency address": "address",
            "producer": "producer_name",
            "producer code": "producer_code",
            "agency code": "additional_data", 
        }
        
        for key, value in all_kvs.items():
            if key in mapping:
                attr = mapping[key]
                if attr == "additional_data":
                    agency.additional_data["agency_code"] = value
                elif getattr(agency, attr) is None:
                    setattr(agency, attr, value)
        return agency

    def _find_policies(self, raw_data: Dict[str, Any], result: ScrapeResult):
        """
        forming data as per Policy model for consistency
        """
        # look for tables with policy information
        all_tables = []
        for section in raw_data.values():
            all_tables.extend(section.get('tables', []))
            
        for table_obj in all_tables:
            rows = table_obj.get("data", [])
            last_policy = None
            for row in rows:
                poly = self._extract_policy_from_row(row, result)
                if poly:
                    last_policy = poly
                elif last_policy and "values" in row:
                    for val_str in row["values"]:
                        parsed = self._parse_mashed_string(val_str)
                        if parsed:
                            last_policy.additional_data.update(parsed)

        # look for lists with policy information      
        for section in raw_data.values():
            for list_obj in section.get('lists', []):
                 for item in list_obj:
                     if isinstance(item, dict):
                         self._extract_policy_from_row(item, result)
                     elif isinstance(item, list):
                         for sub in item:
                             if isinstance(sub, dict):
                                self._extract_policy_from_row(sub, result)

    def _extract_policy_from_row(self, row: Dict[str, str], result: ScrapeResult) -> Optional[Policy]:
        """Helper to check if a dict represents a policy in a table row"""
        keys = [k.lower() for k in row.keys()]
        
        policy_indicators = ["policy", "effective", "expiration", "premium", "coverage", "id"]
        
        is_policy_row = False
        for key in keys:
            for indicator in policy_indicators:
                if indicator in key:
                    is_policy_row = True
                    break
            if is_policy_row:
                break

        if not is_policy_row:
            return None

        has_dates_or_money = False
        for indicator in ["effective", "expiration", "premium", "date"]:
            if indicator in keys:
                has_dates_or_money = True
                break
            
        if "id" in keys and not has_dates_or_money and not "policy" in str(keys):
             return None

        poly = Policy()
        is_poly = False
        
        for k, v in row.items():
            kl = k.lower()
            if "policy" in kl and "number" in kl:
                poly.policy_number = v
                is_poly = True
            elif k.lower() == "id": 
                poly.policy_number = v
                is_poly = True
            elif "effective" in kl:
                poly.effective_date = v
                is_poly = True
            elif "expiration" in kl or "termination" in kl:
                poly.expiration_date = v
            elif "premium" in kl:
                poly.premium = v
                is_poly = True
            elif "carrier" in kl:
                poly.carrier = v
            elif "status" in kl:
                poly.status = v
            else:
                poly.additional_data[k] = v
        
        if is_poly:
            result.policies.append(poly)
            return poly
        return None
