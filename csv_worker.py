import csv

HEADER = ['name','factions','team', 'country']

def read_players(fname = "players_list.csv"):
    d_file = open(fname, "rb")
    
    reader = csv.DictReader(d_file, HEADER, delimiter = ';', restval = '')
    
    data = []
    for line in reader:
        data.append(line)
    
    return data

def write_dummy_data(fname = "players_list.csv"):
    data = [
        {"name": "Joza Skladanka", "factions": "Cygnar", "team": "Brno"}, 
        {"name": "Misa Kunrt", "factions": "Circle, Menoth", "team": "Brno"}, 
      ]
    
    d_file = open(fname, "wb")
    
    writer = csv.DictWriter(d_file, HEADER, delimiter = ';')
    for line in data:
        writer.writerow(line)
        
    d_file.close()
        

if __name__ == "__main__":

    #write_dummy_data()
    for line in read_players_list():
        print line
    
