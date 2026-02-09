import csv
p=r'reports/omitted_from_maps_ci.csv'
with open(p, newline='', encoding='utf-8') as f:
    r=csv.DictReader(f)
    total=0
    no=0
    test=0
    for row in r:
        total+=1
        if row.get('gb__noSpecies','')=='1':
            no+=1
        if row.get('gb__is_test','')=='1':
            test+=1
print(total)
print(no)
print(test)
