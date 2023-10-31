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

import logging, time
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, CallbackContext


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

BOT_TOKEN = '5690693191:AAHBTNpQDPqtJaWeHM5I9NAotBY4JZuGkaA'
# CHAT_ID = '5650214790'

# SOURCE_FOLDER = 'Source_file'
PROCESSINGS_COMMON_FOLDER = 'Processings'
# if not os.path.exists(SOURCE_FOLDER):
#     os.mkdir(SOURCE_FOLDER)
if not os.path.exists(PROCESSINGS_COMMON_FOLDER):
    os.mkdir(PROCESSINGS_COMMON_FOLDER)


#oslistdir = [f for f in os.listdir(SOURCE_FOLDER) if f.partition('.')[2]!='txt'] # remove service-file.txt from list
#SOURCE_PDF_FILE = os.path.join(SOURCE_FOLDER, oslistdir[0])


COUNTER = int()
TIMEOUT_DMTX_DECODE = 100  # dmtx on page - timeout    20 - 2000   10 - 500   5 - 100   1 - 100
log_dict = dict()

def create_processing_folders():
    #
    current_processing_folder = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')
    processing_folder = os.path.join(PROCESSINGS_COMMON_FOLDER, current_processing_folder)
    if os.path.exists(processing_folder):
        processing_folder = os.path.join(PROCESSINGS_COMMON_FOLDER, f'{current_processing_folder}({str(random.randint(1, 100))})')
    source_pdf_file_folder = os.path.join(processing_folder, '1_source_pdf_file')
    pdf_pages_folder = os.path.join(processing_folder, '2_pdf_pages')
    jpg_files_folder = os.path.join(processing_folder, '3_jpg_files')
    res_csv_file = os.path.join(processing_folder, 'res_decoded_dmtx.csv')
    log_file = os.path.join(processing_folder, 'log.txt')

    os.mkdir(processing_folder)
    os.mkdir(source_pdf_file_folder)
    os.mkdir(pdf_pages_folder)
    os.mkdir(jpg_files_folder)
    # shutil.copy(SOURCE_PDF_FILE, source_pdf_file_folder)

    return source_pdf_file_folder, pdf_pages_folder, jpg_files_folder, res_csv_file, log_file


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


def split_pdf_to_pages(source_pdf_file, pdf_pages_folder):
    # load source pdf file and split it to distinct pages
    print('load pdf file ...', end=' ')
    pdf = Pdf.open(source_pdf_file)
    print('ok. source pdf file pages =', len(pdf.pages))

    print('splitting file to distinct pages ...')
    for n, page in enumerate(pdf.pages):
        print(n, end='\r')
        dst = Pdf.new()
        dst.pages.append(page)
        dst.save(f'{pdf_pages_folder}/{n}.pdf')
    print(f'ok. splitted to {n+1} pages')


def convert_pdf_to_jpg(pdf_pages_folder, jpg_files_folder):
    # convert pdf pages to jpg files
    global COUNTER

    pdf_files = os.listdir(pdf_pages_folder)
    pdf_files.sort(key=lambda x: int(x.partition('.')[0]))

    print('converting pdf to jpg ...')
    for file in pdf_files:
        print(file, end='\r')
        image = convert_from_path( os.path.join(pdf_pages_folder, file) )
        COUNTER += 1
        image[0].save(f'{jpg_files_folder}/page'+ str(COUNTER) +'.jpg', 'JPEG')
    print(f'ok. converted {COUNTER} files')


def save_list_to_csv(source_list, res_csv_file):
    # save list to csv file
    rows_for_csv = [ [e] for e in source_list ]

    print('saving results to csv file ...', end=' ')
    with open(res_csv_file, 'w', newline='') as f:
        write = csv.writer(f, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        write.writerows(rows_for_csv)
    print(f'ok. saved to {res_csv_file} file')


def save_log(log, log_file):
    # save file - res records
    print('saving logs ...', end=' ')
    with open(log_file, 'w') as f:
        for k in log:
            rec = f'{k} - decoded {len(log[k])} datamatrixes' + '\n'
            f.write(rec)
    print(f'ok. saved to {log_file} file')


def decode_jpg_dmtx(jpg_files_folder):
    #  decodes datamatrix form jpg file
    general_decode_list = list()
    jpg_files = os.listdir(jpg_files_folder)
    jpg_files.sort(key=lambda x: int(x.partition('.')[0][4:]))

    print('decoding datamartixes ...')
    for file in jpg_files:
        print(file, end='\r')
        image = cv2.imread( os.path.join(jpg_files_folder, file) )
        decode_list = [ r.data.decode() for r in dmtx_lib.decode(image, timeout=TIMEOUT_DMTX_DECODE) ]
        log_dict[file] = decode_list
        general_decode_list += decode_list
    print(f'ok. decoded { len(general_decode_list) } datamartixes')

    return general_decode_list


async def send_file(update, context, file_name):
    # 
    with open(file_name, 'rb') as f:
        await context.bot.send_document(chat_id=update.message.chat_id, document=f)


async def receive_file(update, context):
    #
    msg = update.message

    if not msg.document:
        message_text = 'отправьте файл pdf'
        print(message_text)
        await context.bot.send_message(chat_id=msg.chat_id, text=message_text)
        return 1
    
    if msg.document.mime_type != 'application/pdf':
        message_text = 'некорректный тип файла, не pdf'
        print(message_text)
        await context.bot.send_message(chat_id=msg.chat_id, text=message_text)
        return 1

    source_pdf_file_folder, pdf_pages_folder, jpg_files_folder, res_csv_file, log_file = create_processing_folders()

    f = await context.bot.get_file(update.message.document)
    source_pdf_file = os.path.join(source_pdf_file_folder, msg.document.file_name)
    await f.download_to_drive(custom_path=source_pdf_file)

    message_text = 'принято. ожидайте ответа'
    print(message_text)
    await context.bot.send_message(chat_id=msg.chat_id, text=message_text)

    
    # incoming pdf file handling and decoding of datamatrixes
    split_pdf_to_pages(source_pdf_file, pdf_pages_folder)
    convert_pdf_to_jpg(pdf_pages_folder, jpg_files_folder)
    general_decode_list = decode_jpg_dmtx(jpg_files_folder)
    save_list_to_csv(general_decode_list, res_csv_file)
    save_log(log_dict, log_file)

    await send_file(update, context, file_name=res_csv_file)


##################
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(~filters.COMMAND, receive_file))
    app.run_polling()
