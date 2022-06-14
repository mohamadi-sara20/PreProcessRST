import sys
import os


def seg2berkleyparse(file_path):
    infile = f'{file_path}.txt'
    outfile = f'{file_path}.berkeley'
    os.system(f'java -jar ./BerkeleyParser-1.7.jar -gr ./ger_sm5.gr -inputFile {infile} -outputFile {outfile}')



def txt2parzuparse(file_path):
    infile = f'{file_path}.txt'
    outfile = f'{file_path}.parzu'
    os.system(f'cat {infile} | docker run -i rsennrich/parzu /ParZu/parzu >> {outfile}')


if __name__ == "__main__":
    print('====================== text 2 parse =================')
    path = sys.argv[1]
    if path.endswith('/'):
        path = path[:len(path)-1]
    all_files = os.listdir(path)
    for filename in sorted(all_files):
        if not filename.endswith('.segment'):
            continue
        filename = filename.split('.segment')[0]
        try:
            print(filename)
            seg2berkleyparse(f'{path}/{filename}')
            txt2parzuparse(f'{path}/{filename}')
        except Exception as ex:
            print('###################################################')
            print(filename)
            print(ex)

