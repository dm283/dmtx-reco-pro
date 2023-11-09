import os, sys, random, configparser, logging, time
from pikepdf import Pdf
from pdf2image import convert_from_path
import pylibdmtx.pylibdmtx as dmtx_lib, cv2, datetime, os, sys, csv
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from pathlib import Path

config = configparser.ConfigParser()
config_file = os.path.join(Path(__file__).resolve().parent, 'config.ini')
if os.path.exists(config_file):
  config.read(config_file, encoding='utf-8')
else:
  print("error! config file doesn't exist"); sys.exit()

BOT_TOKEN = config['telegram_bot']['bot_token']
TELEGRAM_SERVER = config['telegram_bot']['telegram_server']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PROCESSINGS_COMMON_FOLDER = 'Processings'
if not os.path.exists(PROCESSINGS_COMMON_FOLDER):
    os.mkdir(PROCESSINGS_COMMON_FOLDER)
TIMEOUT_LIST = [100, 500, 2000, 5000, 10000, 20000, 30000, 50000, None]


def create_processing_folders():
    # creates folders for current processing
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

    return source_pdf_file_folder, pdf_pages_folder, jpg_files_folder, res_csv_file, log_file


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
    counter = int()

    pdf_files = os.listdir(pdf_pages_folder)
    pdf_files.sort(key=lambda x: int(x.partition('.')[0]))

    print('converting pdf to jpg ...')
    for file in pdf_files:
        print(file, end='\r')
        image = convert_from_path( os.path.join(pdf_pages_folder, file) )
        image[0].save(f'{jpg_files_folder}/page'+ str(counter) +'.jpg', 'JPEG')
        counter += 1
    print(f'ok. converted {counter} files')


def save_list_to_csv(source_list, res_csv_file):
    # save list to csv file
    rows_for_csv = [ [e] for e in source_list ]

    print('saving results to csv file ...', end=' ')
    with open(res_csv_file, 'w', newline='') as f:
        write = csv.writer(f, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        write.writerows(rows_for_csv)
    print(f'ok. saved to {res_csv_file} file')


def save_log(log_dict, log_file):
    # save file - res records
    print('saving logs ...', end=' ')
    with open(log_file, 'w') as f:
        for k in log_dict:
            rec = f'{k} - decoded {len(log_dict[k])} datamatrixes' + '\n'
            f.write(rec)
    print(f'ok. saved to {log_file} file')


def decode_jpg_dmtx(jpg_files_folder, timeout_dmtx_decode, dmtx_cnt_per_page):
    #  decodes datamatrix form jpg file
    general_decode_list = list()
    log_dict = dict()
    jpg_files = os.listdir(jpg_files_folder)
    jpg_files.sort(key=lambda x: int(x.partition('.')[0][4:]))

    print('decoding datamartixes ...')
    for file in jpg_files:
        # print(file, end='\r')
        print(file, end=' ')
        image = cv2.imread( os.path.join(jpg_files_folder, file) )

        # decode_list = [ r.data.decode() for r in dmtx_lib.decode(image, timeout=timeout_dmtx_decode) ]

        timeout = timeout_dmtx_decode
        decode_list = list()
        # TIMEOUT_LIST = [100, 500, 2000, 5000, 10000, 20000, 30000, 50000, None]
        timeout_list_pointer = TIMEOUT_LIST.index(timeout_dmtx_decode)
        while len(decode_list) < dmtx_cnt_per_page:
            decode_list = [ r.data.decode() for r in dmtx_lib.decode(image, timeout=timeout) ]
            print( 'decoded elements =', len(decode_list) )
            if len(decode_list) < dmtx_cnt_per_page:
                timeout_list_pointer += 1
                if (timeout_list_pointer + 1) <= len(TIMEOUT_LIST):
                    timeout = TIMEOUT_LIST[timeout_list_pointer]
                    print(file, f'increase timeout to {timeout}')
                    print(file, end=' ')
                else:
                    print(file, 'maximum timeout')
                    break


        log_dict[file] = decode_list
        general_decode_list += decode_list
    print(f'ok. decoded { len(general_decode_list) } datamartixes')

    return general_decode_list, log_dict


def timeout_count(caption):
    # checks correct format of caption and estimates timeout for dmtx decoding
    try:
        dmtx_cnt_per_page = int(caption)
        if dmtx_cnt_per_page < 1:
            raise Exception
    except:
        return 'err', None, None

    #TIMEOUT_DMTX_DECODE = 2000  # dmtx on page - timeout    20 - 2000   10 - 500   5 - 100   1 - 100
    if dmtx_cnt_per_page <= 20:
        timeout_dmtx_decode = 2000
    if dmtx_cnt_per_page <= 10:
        timeout_dmtx_decode = 500
    if dmtx_cnt_per_page <= 5:
        timeout_dmtx_decode = 100
    if dmtx_cnt_per_page > 20:
        timeout_dmtx_decode = None
    print(f'dmtx_quantity = {dmtx_cnt_per_page}  timeout = {timeout_dmtx_decode}')

    return 'ok', timeout_dmtx_decode, dmtx_cnt_per_page


async def run_script(update, context):
    # main function
    msg = update.message

    if not msg.document:
        message_text = 'ошибка. отправьте файл pdf'
        print(message_text)
        await context.bot.send_message(chat_id=msg.chat_id, text=message_text)
        return 1
    
    if msg.document.mime_type != 'application/pdf':
        message_text = 'ошибка. некорректный тип файла, не pdf'
        print(message_text)
        await context.bot.send_message(chat_id=msg.chat_id, text=message_text)
        return 1

    caption = msg.caption
    res, timeout_dmtx_decode, dmtx_cnt_per_page = timeout_count(caption)
    if res == 'err':
        message_text = 'ошибка. в подписи к файлу не указано/ошибочное кол-во элементов на странице'
        print(message_text)
        await context.bot.send_message(chat_id=msg.chat_id, text=message_text)
        return 1

    print('run script')
    source_pdf_file_folder, pdf_pages_folder, jpg_files_folder, res_csv_file, log_file = create_processing_folders()

    # download file from telegram
    f = await context.bot.get_file(update.message.document)
    source_pdf_file = os.path.join(source_pdf_file_folder, msg.document.file_name)
    await f.download_to_drive(custom_path=source_pdf_file, read_timeout=2000.0)
    message_text = 'принято. ожидайте ответа'
    print(message_text)
    await context.bot.send_message(chat_id=msg.chat_id, text=message_text)

    # incoming pdf file handling and decoding of datamatrixes
    split_pdf_to_pages(source_pdf_file, pdf_pages_folder)
    convert_pdf_to_jpg(pdf_pages_folder, jpg_files_folder)
    general_decode_list, log_dict = decode_jpg_dmtx(jpg_files_folder, timeout_dmtx_decode, dmtx_cnt_per_page)
    save_list_to_csv(general_decode_list, res_csv_file)
    save_log(log_dict, log_file)

    # sends outcome file from bot to customer
    with open(res_csv_file, 'rb') as f:
        await context.bot.send_document(chat_id=update.message.chat_id, document=f)


##################
if __name__ == '__main__':
    if TELEGRAM_SERVER == 'official':
        app = ApplicationBuilder().token(BOT_TOKEN).build()
    elif TELEGRAM_SERVER == 'local':
        app = ApplicationBuilder()
        app = app.token(BOT_TOKEN)
        app = app.base_url('http://localhost:8081/bot')
        app = app.base_file_url('http://localhost:8081/file/bot')
        app = app.build()
    app.add_handler(MessageHandler(~filters.COMMAND, run_script))
    app.run_polling()
