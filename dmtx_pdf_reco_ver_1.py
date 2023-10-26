# it's necessary to download 'poppler' for Windows and define system PATH
# в папку SOURCE_PDF_FILE_FOLDER помещается pdf-файл с датаматриксами
# split_pdf_to_pages() загружает pdf-файл и разбивает его на отдельные страницы (pdf-файлы), сохраняя их в папку PDF_PAGES_FOLDER
# convert_pdf_to_jpg() конвертирует pdf-файлы в jpg и сохраняет их в папку JPG_FILES_FOLDER
# decode_jpg_dmtx() загружает jpg-файлы из JPG_FILES_FOLDER и декодирует датаматриксы из них
# save_list_to_csv() сохраняет результаты декодирования в csv-файл
# save_log() логирует работу скрипта

import os, sys, random, shutil
from pikepdf import Pdf
from pdf2image import convert_from_path
import pylibdmtx.pylibdmtx as dmtx_lib, cv2, datetime, os, sys, csv


SOURCE_FOLDER = 'Source_file'
oslistdir = [f for f in os.listdir(SOURCE_FOLDER) if f.partition('.')[2]!='txt'] # remove service-file.txt
SOURCE_PDF_FILE = os.path.join(SOURCE_FOLDER, oslistdir[0])
PROCESSINGS_COMMON_FOLDER = 'Processings'

COUNTER = int()
TIMEOUT_DMTX_DECODE = 100  # dmtx on page - timeout    20 - 2000   10 - 500   5 - 100   1 - 100
log_dict = dict()

current_processing_folder = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')
PROCESSING_FOLDER = os.path.join(PROCESSINGS_COMMON_FOLDER, current_processing_folder)
if os.path.exists(PROCESSING_FOLDER):
    PROCESSING_FOLDER = os.path.join(PROCESSINGS_COMMON_FOLDER, f'{current_processing_folder}({str(random.randint(1, 100))})')
SOURCE_PDF_FILE_FOLDER = os.path.join(PROCESSING_FOLDER, '1_source_pdf_file')
PDF_PAGES_FOLDER = os.path.join(PROCESSING_FOLDER, '2_pdf_pages')
JPG_FILES_FOLDER = os.path.join(PROCESSING_FOLDER, '3_jpg_files')
RES_CSV_FILE = os.path.join(PROCESSING_FOLDER, 'res_decoded_dmtx.csv')
LOG_FILE = os.path.join(PROCESSING_FOLDER, 'log.txt')
if not os.path.exists(PROCESSINGS_COMMON_FOLDER):
    os.mkdir(PROCESSINGS_COMMON_FOLDER)
os.mkdir(PROCESSING_FOLDER)
os.mkdir(SOURCE_PDF_FILE_FOLDER)
os.mkdir(PDF_PAGES_FOLDER)
os.mkdir(JPG_FILES_FOLDER)
shutil.copy(SOURCE_PDF_FILE, SOURCE_PDF_FILE_FOLDER)


# def folder_is_empty_check(folder):
#     # checks folder is empty
#     if len( os.listdir(folder) ) > 0:
#         print(f'folder [{folder}] is not empty! -> app is stopped')
#         sys.exit()


# def file_exists_check(file):
#     # checks file exists
#     if os.path.exists(file):
#         print(f'file [{file}] exists! -> app is stopped')
#         sys.exit()


def split_pdf_to_pages(source_pdf_file):
    # load source pdf file and split it to distinct pages
    print('load pdf file ...', end=' ')
    pdf = Pdf.open(source_pdf_file)
    print('ok. source pdf file pages =', len(pdf.pages))

    print('splitting file to distinct pages ...')
    for n, page in enumerate(pdf.pages):
        print(n, end='\r')
        dst = Pdf.new()
        dst.pages.append(page)
        dst.save(f'{PDF_PAGES_FOLDER}/{n}.pdf')
    print(f'ok. splitted to {n+1} pages')


def convert_pdf_to_jpg():
    # convert pdf pages to jpg files
    global COUNTER

    pdf_files = os.listdir(PDF_PAGES_FOLDER)
    pdf_files.sort(key=lambda x: int(x.partition('.')[0]))

    print('converting pdf to jpg ...')
    for file in pdf_files:
        print(file, end='\r')
        image = convert_from_path( os.path.join(PDF_PAGES_FOLDER, file) )
        COUNTER += 1
        image[0].save(f'{JPG_FILES_FOLDER}/page'+ str(COUNTER) +'.jpg', 'JPEG')
    print(f'ok. converted {COUNTER} files')


def save_list_to_csv(source_list):
    # save list to csv file
    rows_for_csv = [ [e] for e in source_list ]

    print('saving results to csv file ...', end=' ')
    with open(RES_CSV_FILE, 'w', newline='') as f:
        write = csv.writer(f, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        write.writerows(rows_for_csv)
    print(f'ok. saved to {RES_CSV_FILE} file')


def save_log(log):
    # save file - res records
    print('saving logs ...', end=' ')
    with open(LOG_FILE, 'w') as f:
        for k in log:
            rec = f'{k} - decoded {len(log[k])} datamatrixes' + '\n'
            f.write(rec)
    print(f'ok. saved to {LOG_FILE} file')


def decode_jpg_dmtx():
    #  decodes datamatrix form jpg file
    general_decode_list = list()
    jpg_files = os.listdir(JPG_FILES_FOLDER)
    jpg_files.sort(key=lambda x: int(x.partition('.')[0][4:]))

    print('decoding datamartixes ...')
    for file in jpg_files:
        print(file, end='\r')
        image = cv2.imread( os.path.join(JPG_FILES_FOLDER, file) )
        decode_list = [ r.data.decode() for r in dmtx_lib.decode(image, timeout=TIMEOUT_DMTX_DECODE) ]
        log_dict[file] = decode_list
        general_decode_list += decode_list
    print(f'ok. decoded { len(general_decode_list) } datamartixes')

    return general_decode_list


############
# folder_is_empty_check(PDF_PAGES_FOLDER)
# folder_is_empty_check(JPG_FILES_FOLDER)
# file_exists_check(RES_CSV_FILE)

split_pdf_to_pages(SOURCE_PDF_FILE)
convert_pdf_to_jpg()

general_decode_list = decode_jpg_dmtx()
save_list_to_csv(general_decode_list)
save_log(log_dict)
