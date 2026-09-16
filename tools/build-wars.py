#!/usr/bin/env python3
"""Bake the world's ongoing wars into the Esquiffis page's map (the "Wars" layer).

    python3 tools/build-wars.py            # rewrite the list in index.html
    python3 tools/build-wars.py --dry-run  # print it, touch nothing

Reads Wikipedia's "List of ongoing armed conflicts" - the Major wars table (10,000+ combat deaths in the current or
previous year) and the Minor wars table (1,000-9,999) - and maps each conflict's Location countries to ISO3 codes
through the SAME countries GeoJSON the page draws (johan/world.geo.json on jsDelivr, CORS *), so every code here has
a polygon there. Writes the list between /*WARS-BEGIN*/ and /*WARS-END*/ in index.html, dated. The page fetches
nothing but the countries file: 0 n8n executions. Re-run whenever the list should catch up with the world.
Countries the 110m file has no polygon for (Bahrain, Singapore, small islands) are reported and skipped.
"""
import json, pathlib, re, sys, urllib.request, datetime

HERE = pathlib.Path(__file__).resolve().parent.parent
WIKI = ('https://en.wikipedia.org/w/api.php?action=parse&page=List_of_ongoing_armed_conflicts'
        '&prop=wikitext&format=json&formatversion=2&origin=*')
COUNTRIES = 'https://cdn.jsdelivr.net/gh/johan/world.geo.json@master/countries.geo.json'
ALIAS = {   # Wikipedia flag names -> the GeoJSON's English names (or a code the page knows)
    'Palestine': 'PSE', 'State of Palestine': 'PSE', 'Palestinian territories': 'PSE', 'Gaza Strip': 'GAZA', 'Gaza': 'GAZA',
    'West Bank': 'PSE', 'DR Congo': 'Democratic Republic of the Congo', 'DRC': 'Democratic Republic of the Congo',
    'Democratic Republic of Congo': 'Democratic Republic of the Congo', 'Congo': 'Republic of the Congo',
    'Burma': 'Myanmar', 'Türkiye': 'Turkey', 'Turkiye': 'Turkey', 'Czechia': 'Czech Republic', "Côte d'Ivoire": 'Ivory Coast',
    'Cote d\'Ivoire': 'Ivory Coast', 'Eswatini': 'Swaziland', 'North Macedonia': 'Macedonia', 'Timor-Leste': 'East Timor',
    'Somaliland': 'Somalia', 'Puntland': 'Somalia', 'Kurdistan Region': 'Iraq', 'Iraqi Kurdistan': 'Iraq', 'Rojava': 'Syria',
    'United States': 'United States of America', 'USA': 'United States of America', 'UK': 'United Kingdom', 'Sahrawi Arab Democratic Republic': 'Western Sahara',
    'Serbia': 'Republic of Serbia', 'Tanzania': 'United Republic of Tanzania', 'Bahamas': 'The Bahamas', 'Guinea-Bissau': 'Guinea Bissau',
    'Cabo Verde': 'Cape Verde', 'Republic of the Congo': 'Republic of the Congo', 'South Korea': 'South Korea', 'North Korea': 'North Korea',
    'Bosnia': 'Bosnia and Herzegovina', 'Central African Republic': 'Central African Republic', 'Federated States of Micronesia': 'Micronesia',
}
NO_POLYGON = {'Bahrain', 'Singapore', 'Maldives', 'Comoros', 'Mauritius', 'Seychelles', 'Malta', 'Kiribati', 'Tuvalu', 'Nauru',
              'Marshall Islands', 'Micronesia', 'Palau', 'Samoa', 'Tonga', 'Grenada', 'Barbados', 'Saint Lucia', 'Dominica',
              'Antigua and Barbuda', 'Saint Kitts and Nevis', 'Saint Vincent and the Grenadines', 'Liechtenstein', 'Monaco',
              'San Marino', 'Andorra', 'Vatican City', 'Hong Kong', 'Macau', 'Cape Verde'}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'esquiffis-hub build-wars (fer.villasana14@gmail.com)'}), timeout=60).read()


def rows_of(section):
    k = section.find('{|')
    body = section[k:] if k >= 0 else ''
    body = body[:body.find('\n|}')] if '\n|}' in body else body
    parts = re.split(r'\n\|-[^\n]*', body)
    out = []
    for part in parts[1:]:
        cells = re.split(r'\n\|', '\n' + part.strip('\n'))
        cells = [c for c in cells if c.strip() != '']
        if len(cells) < 4 or cells[0].lstrip().startswith('!'):
            continue
        out.append(cells)
    return out


def links(text):
    return [(m.group(1).strip(), (m.group(2) or m.group(1)).strip()) for m in re.finditer(r'\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]', text)]


def conflict_name(cell):
    # the top-level bullet(s) of the tree list, by the linked article's title (the display text can be a bare "Aftermath")
    tops = [ln for ln in cell.split('\n') if re.match(r'^\*\s', ln)]
    names = []
    for ln in tops[:2]:
        ls = links(ln)
        if ls:
            names.append(re.sub(r'\s*\((disambiguation|\d{4}[^)]*present)\)\s*$', '', re.sub(r'\s+', ' ', ls[0][0])))
    if not names:
        ls = links(cell)
        names = [ls[0][1]] if ls else [re.sub(r'\{\{.*?\}\}|<.*?>', '', cell).strip()[:60]]
    return ' / '.join(names)[:70]


def countries_of(cell):
    names = re.findall(r'\{\{(?:flag|flagcountry|flagicon|FLAG|Flag|flagu|flagdeco|flaglist)\|([^}|]+)', cell)
    names += [t for t, _ in links(cell)]
    seen, out = set(), []
    for n in names:
        n = n.strip()
        if n and n not in seen:
            seen.add(n); out.append(n)
    return out


def number(cell):
    m = re.search(r'\{\{nts\|([\d,]+)', cell)
    return int(m.group(1).replace(',', '')) if m else None


def main():
    dry = '--dry-run' in sys.argv
    wikitext = json.loads(get(WIKI))['parse']['wikitext']
    geo = json.loads(get(COUNTRIES))
    by_name = {f['properties']['name']: f['id'] for f in geo['features']}
    by_code = {f['id'] for f in geo['features']}

    def code_for(name):
        if name in NO_POLYGON:
            return None
        n = ALIAS.get(name, name)
        if n in by_code or n == 'GAZA':
            return n
        if n in by_name:
            return by_name[n]
        return '?' + name

    wars, unmatched = [], set()
    for tier, heading in (('major', '==Major wars'), ('minor', '==Minor wars')):
        i = wikitext.find(heading)
        j = wikitext.find('\n==', i + 10)
        section = wikitext[i:j]
        for cells in rows_of(section):
            year = re.search(r'(\d{4})', cells[0])
            codes = []
            for cname in countries_of(cells[3]):
                c = code_for(cname)
                if c is None:
                    continue
                if c.startswith('?'):
                    unmatched.add(cname); continue
                if c not in codes:
                    codes.append(c)
            if not codes:
                continue
            wars.append({'n': conflict_name(cells[1]), 't': tier, 'y': int(year.group(1)) if year else None, 'c': codes,
                         'd': number(cells[6]) if len(cells) > 6 else None})
    today = datetime.date.today().isoformat()
    block = '/*WARS-BEGIN*/\n  var WARS_DATE=%s, WARS=%s;\n  /*WARS-END*/' % (json.dumps(today), json.dumps(wars, ensure_ascii=False, separators=(',', ':')))
    print('%d wars (%d major, %d minor), %d countries; unmatched names: %s' % (
        len(wars), sum(w['t'] == 'major' for w in wars), sum(w['t'] == 'minor' for w in wars),
        len({c for w in wars for c in w['c']}), sorted(unmatched) or 'none'))
    for w in wars:
        print('  %-5s %s  %s  %s  %s' % (w['t'], w['y'], w['n'], ','.join(w['c']), w['d']))
    if dry:
        return
    page_path = HERE / 'index.html'
    page = page_path.read_text()
    B, E = '/*WARS-BEGIN*/', '/*WARS-END*/'
    assert page.count(B) == 1 and page.count(E) == 1, 'page markers missing'
    page_path.write_text(page[:page.index(B)] + block + page[page.index(E) + len(E):])
    print('written to index.html, dated', today)


if __name__ == '__main__':
    main()
