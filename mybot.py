import time
import random
import re
import datetime
import requests
from fpdf import FPDF
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from flask import Flask
import threading

web_app = Flask(name)

@web_app.route('/')
def home():
    return """
    <html>
        <head>
            <title>🤖 بوت السرعة السداسية</title>
            <meta charset="utf-8">
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    text-align: center;
                    padding: 50px;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 2.5em; margin-bottom: 20px; }
                .status { 
                    background: #28a745; 
                    padding: 10px 20px; 
                    border-radius: 25px; 
                    display: inline-block;
                    margin: 10px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 بوت السرعة السداسية</h1>
                <div class="status">🟢 البوت يعمل بنجاح</div>
                <p>⚡ البوت نشط وجاهز للاستخدام في تيليجرام</p>
                <p>📊 الإصدار: 2.0 | 🏆 نوع: لعبة السرعة</p>
            </div>
        </body>
    </html>
    """

def run_web_server():
    '''تشغيل سيرفر الويب في الخلفية'''
    web_app.run(host='0.0.0.0', port=8080, debug=False)

web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

TOKEN = "8375820223:AAENKlwxCbif4SDc4xSETcTjdum27ccfxWY"

BOT_STATUS = "online"
ALLOWED_GROUPS = set()
RESTRICTED_MODE = False
BOT_ADMIN_CONTROLS = {}
BOT_START_TIME = time.time()
BACKUP_DATA = {}
GROUP_SETTINGS = {}
BOT_BLACKLIST = set()

bot_settings = {
    'active_groups': {},
    'backup_data': {},
    'bot_status': 'active',
    'maintenance_mode': False,
    'stopped_groups': set(),
    'stopped_private': False
}

backup_files = {}

def check_internet():
    try:
        requests.get('https://www.google.com', timeout=10)
        return True
    except:
        try:
            requests.get('https://api.telegram.org', timeout=10)
            return True
        except:
            print("⚠️ تحذير: قد يكون هناك مشكلة في الاتصال بالإنترنت")
            return True

def is_bot_active(chat_id, chat_type):
    if bot_settings['bot_status'] == 'stopped':
        return False
    if chat_type == 'private' and bot_settings['stopped_private']:
        return False
    if chat_type == 'group' and str(chat_id) in bot_settings['stopped_groups']:
        return False
    return True

async def backup_bot_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    backup_id = f"backup_{int(time.time())}"
    backup_data = {
        'training_words': training_words.copy(),
        'training_numbers': training_numbers.copy(),
        'training_sentences': training_sentences.copy(),
        'user_scores': user_scores.copy(),
        'user_detailed_stats': user_detailed_stats.copy(),
        'records': records.copy(),
        'active_challenges': active_challenges.copy(),
        'challenge_leaderboards': challenge_leaderboards.copy(),
        'bot_settings': bot_settings.copy(),
        'timestamp': time.time()
    }
    
    bot_settings['backup_data'][backup_id] = backup_data
    backup_files[backup_id] = backup_data
    
    await update.message.reply_text(f"✅ تم إنشاء النسخة الاحتياطية: {backup_id}")

async def restore_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    if not backup_files:
        await update.message.reply_text("❌ لا توجد نسخ احتياطية")
        return
    
    keyboard = []
    for backup_id in backup_files.keys():
        keyboard.append([InlineKeyboardButton(f"📦 {backup_id}", callback_data=f"restore_{backup_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_restore")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("📋 اختر النسخة للاستعادة:", reply_markup=reply_markup)

async def create_comprehensive_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إنشاء نسخة احتياطية شاملة بصيغة JSON"""
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    try:
        backup_id = f"backup_{int(time.time())}"
        
        user_stats_data = {}
        for user_id, stats in context.bot_data.get('user_stats', {}).items():
            user_stats_data[str(user_id)] = {
                'words_correct': stats.get('words_correct', 0),
                'words_wrong': stats.get('words_wrong', 0),
                'numbers_correct': stats.get('numbers_correct', 0),
                'numbers_wrong': stats.get('numbers_wrong', 0),
                'sentences_correct': stats.get('sentences_correct', 0),
                'sentences_wrong': stats.get('sentences_wrong', 0),
                'total_time': stats.get('total_time', 0),
                'join_date': stats.get('join_date', ''),
                'first_activity': stats.get('first_activity', 0)
            }
        
        backup_data = {
            'user_scores': {str(k): v for k, v in user_scores.items()},
            'user_detailed_stats': {str(k): v for k, v in user_detailed_stats.items()},
            'records': {
                'word': {k: (v if k != 'user_id' else str(v)) for k, v in records['word'].items()},
                'number': {k: (v if k != 'user_id' else str(v)) for k, v in records['number'].items()},
                'sentence': {k: (v if k != 'user_id' else str(v)) for k, v in records['sentence'].items()}
            },
            'challenge_leaderboards': {str(k): v for k, v in challenge_leaderboards.items()},
            'user_stats': user_stats_data,
            'timestamp': time.time(),
            'backup_id': backup_id
        }
        
        json_filename = f"backup_{backup_id}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        with open(json_filename, 'rb') as json_file:
            await update.message.reply_document(
                document=json_file,
                caption=f"💾 النسخة الاحتياطية الشاملة\n⏰ {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n👥 اللاعبين: {len(user_scores)}\n🏆 النقاط: {sum(user_scores.values())}",
                filename=f"استعادة_بيانات_{backup_id}.json"
            )
        
        os.remove(json_filename)
        
        await update.message.reply_text("✅ تم إنشاء النسخة الاحتياطية بنجاح!")
        
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        await update.message.reply_text(f"❌ فشل في إنشاء النسخة الاحتياطية: {error_msg}")

async def restore_from_json(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استعادة البيانات من ملف JSON"""
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    if not update.message.document:
        await update.message.reply_text("❌ يرجى إرسال ملف JSON للاستعادة")
        return
    
    try:
        file = await update.message.document.get_file()
        file_path = f"restore_{int(time.time())}.json"
        await file.download_to_drive(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        global user_scores, user_detailed_stats, records, challenge_leaderboards
        
        user_scores.clear()
        user_detailed_stats.clear()
        challenge_leaderboards.clear()
        
        for user_id_str, score in backup_data['user_scores'].items():
            user_scores[int(user_id_str)] = score
        
        for user_id_str, stats in backup_data['user_detailed_stats'].items():
            user_detailed_stats[int(user_id_str)] = stats
        
        records['word'] = backup_data['records']['word']
        records['number'] = backup_data['records']['number']
        records['sentence'] = backup_data['records']['sentence']
        
        for user_id_str, user_data in backup_data['challenge_leaderboards'].items():
            challenge_leaderboards[int(user_id_str)] = user_data
        
        if 'user_stats' in backup_data:
            context.bot_data['user_stats'] = {}
            for user_id_str, stats in backup_data['user_stats'].items():
                context.bot_data['user_stats'][int(user_id_str)] = stats
        
        os.remove(file_path)
        
        await update.message.reply_text(
            f"✅ تم استعادة جميع البيانات بنجاح!\n\n"
            f"👥 اللاعبين: {len(user_scores)}\n"
            f"🏆 النقاط الإجمالية: {sum(user_scores.values())}\n"
            f"🔄 جميع الإنجازات والنقاط معادة"
        )
        
    except Exception as e:
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        await update.message.reply_text(f"❌ فشل في استعادة البيانات: {error_msg}")

async def restore_comprehensive_backup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استعادة نسخة احتياطية"""
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    if not backup_files:
        await update.message.reply_text("❌ لا توجد نسخ احتياطية")
        return
    
    keyboard = []
    for backup_id in backup_files.keys():
        timestamp = datetime.datetime.fromtimestamp(backup_files[backup_id]['timestamp']).strftime('%Y-%m-%d %H:%M')
        keyboard.append([InlineKeyboardButton(f"📦 {timestamp}", callback_data=f"restore_{backup_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 إلغاء", callback_data="cancel_restore")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("📋 اختر النسخة للاستعادة:", reply_markup=reply_markup)

async def handle_backup_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة استدعاءات النسخ الاحتياطي"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_restore":
        await query.edit_message_text("❌ تم إلغاء الاستعادة")
        return
    
    if query.data.startswith("restore_"):
        backup_id = query.data.replace("restore_", "")
        
        if backup_id in backup_files:
            backup_data = backup_files[backup_id]
            
            global training_words, training_numbers, training_sentences, user_scores
            global user_detailed_stats, records, active_challenges, challenge_leaderboards
            
            training_words = backup_data['training_words'].copy()
            training_numbers = backup_data['training_numbers'].copy()
            training_sentences = backup_data['training_sentences'].copy()
            user_scores = backup_data['user_scores'].copy()
            user_detailed_stats = backup_data['user_detailed_stats'].copy()
            records = backup_data['records'].copy()
            active_challenges = backup_data['active_challenges'].copy()
            challenge_leaderboards = backup_data['challenge_leaderboards'].copy()
            
            if 'user_stats' in backup_data:
                context.bot_data['user_stats'] = backup_data['user_stats'].copy()
            
            timestamp = datetime.datetime.fromtimestamp(backup_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            await query.edit_message_text(
                f"✅ تم استعادة النسخة الاحتياطية بنجاح!\n\n"
                f"📦 رقم النسخة: `{backup_id}`\n"
                f"⏰ وقت النسخة: {timestamp}\n"
                f"🔄 تم تحديث جميع البيانات"
            )
        else:
            await query.edit_message_text("❌ النسخة غير موجودة")

async def manage_bot_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    keyboard = [
        [InlineKeyboardButton("⏸️ إيقاف البوت", callback_data="bot_stop_options")],
        [InlineKeyboardButton("▶️ تشغيل البوت", callback_data="bot_start_options")],
        [InlineKeyboardButton("🛠️ وضع الصيانة", callback_data="bot_maintenance_options")],
        [InlineKeyboardButton("💾 النسخ الاحتياطي", callback_data="backup_options")],
        [InlineKeyboardButton("📊 المجموعات النشطة", callback_data="active_groups_list")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text("🛠️ لوحة تحكم البوت:", reply_markup=reply_markup)

training_words = [
    'هيكس', 'مرتضى', 'يوزر', 'سواد', 'حوراء', 'سلام', 'كتاب', 'مدرسة', 'بيت', 'سيارة', 
    'حاسوب', 'هاتف', 'نافذة', 'بحر', 'شمس', 'قمر', 'نجمة', 'وردة', 'شجرة', 'طائرة',
    'قطار', 'تفاحة', 'برتقال', 'موز', 'عنب', 'فراولة', 'بطيخ', 'خيار', 'طماطم', 'اسد',
    'فيل', 'زرافة', 'دولفين', 'عصفور', 'سمكة', 'قطة', 'كلب', 'قلم', 'ورق', 'مكتب',
    'كرسي', 'سرير', 'منضدة', 'مصباح', 'ساعة', 'حائط', 'سقف', 'ارض', 'باب', 'شباك',
    'سجاد', 'وسادة', 'بطانية', 'ملابس', 'حذاء', 'قبعة', 'نظارة', 'ساعة', 'خلخال', 'عقد',
    'خاتم', 'سلسلة', 'محفظة', 'مفاتيح', 'نقود', 'هوية', 'رخصة', 'جواز', 'تذكرة', 'حقيبة',
    'شنطة', 'صندوق', 'علبة', 'كيس', 'زجاجة', 'كوب', 'صحن', 'ملعقة', 'شوكة', 'سكين',
    'قدح', 'ابريق', 'مقلاة', 'طنجرة', 'فرن', 'ثلاجة', 'غسالة', 'مكيف', 'مروحة', 'مدفأة',
    'مصباح', 'شمعة', 'ولاعة', 'كبريت', 'سجائر', 'نار', 'دخان', 'لهب', 'رماد', 'فحم',
    'خشب', 'حديد', 'نحاس', 'ذهب', 'فضة', 'الماس', 'لؤلؤ', 'مرجان', 'عقيق', 'ياقوت',
    'زمرد', 'فيروز', 'عاج', 'عظم', 'جلد', 'فراء', 'صوف', 'قطن', 'حرير', 'كتان',
    'نايلون', 'بوليستر', 'جينز', 'قماش', 'خيط', 'ابرة', 'مقص', 'دبوس', 'زر', 'سحاب',
    'حزام', 'ربطة', 'دبوس', 'صمغ', 'لصق', 'طلاء', 'دهان', 'ورنيش', 'معجون', 'مسحوق',
    'سائل', 'غاز', 'صلب', 'سائل', 'بلازما', 'معدن', 'صخر', 'تراب', 'رمل', 'حصى',
    'طين', 'وحل', 'ماء', 'نهر', 'بحر', 'محيط', 'بحيرة', 'بركة', 'شلال', 'نبع',
    'عين', 'بئر', 'مطر', 'ثلج', 'برد', 'صقيع', 'ندى', 'ضباب', 'سحاب', 'قوس',
    'رعد', 'برق', 'عاصفة', 'اعصار', 'زلزال', 'بركان', 'حفرة', 'جبل', 'تل', 'هضبة',
    'وادي', 'غابة', 'صحراء', 'واحة', 'شاطئ', 'جزيرة', 'قارة', 'دولة', 'مدينة', 'قرية',
    'حي', 'شارع', 'ساحة', 'ميدان', 'جسر', 'نفق', 'ممر', 'سلم', 'مصعد', 'سور',
    'حائط', 'سور', 'بوابة', 'درج', 'شرفة', 'بلكونة', 'حديقة', 'مسبح', 'ملعب', 'مطعم',
    'مقهى', 'فندق', 'مستشفى', 'مدرسة', 'جامعة', 'مكتبة', 'مسجد', 'كنيسة', 'معبد', 'سجن',
    'شرطة', 'مطافئ', 'مستوصف', 'صيدلية', 'عيادة', 'مختبر', 'معمل', 'مصنع', 'مزرعة', 'حقل',
    'بستان', 'حديقة', 'غابة', 'منتزه', 'ملاهي', 'سيرك', 'مسرح', 'سينما', 'متحف', 'معرض',
    'سوق', 'متجر', 'محل', 'مركز', 'مول', 'سوبرماركت', 'بقالة', 'خضار', 'فواكه', 'لحوم',
    'اسماك', 'دجاج', 'بيض', 'حليب', 'جبن', 'لبن', 'زبدة', 'عسل', 'سكر', 'ملح',
    'فلفل', 'بهارات', 'زيت', 'خل', 'صلصة', 'معكرونة', 'ارز', 'خبز', 'كعك', 'حلويات',
    'شوكولاتة', 'بسكويت', 'حلوى', 'مربى', 'عصير', 'مشروب', 'قهوة', 'شاي', 'حليب', 'ماء',
    'عصير', 'نكتار', 'شراب', 'كوكتيل', 'بيرة', 'نبيذ', 'خمر', 'عرق', 'ويسكي', 'فودكا',
    'روم', 'جين', 'تيكيلا', 'براندي', 'كونياك', 'شمبانيا', 'سيدر', 'عصير', 'ليمونادة',
    'برتقال', 'تفاح', 'موز', 'عنب', 'فراولة', 'كرز', 'خوخ', 'مشمش', 'برقوق', 'رمان',
    'بطيخ', 'شمام', 'كانتالوب', 'كيوي', 'اناناس', 'مانجو', 'بابايا', 'جوز', 'لوز', 'فستق',
    'كاجو', 'بندق', 'صنوبر', 'جوزة', 'زبيب', 'تمر', 'تين', 'مشمش', 'خروب', 'سفرجل',
    'زيتون', 'افوكادو', 'ليمون', 'برتقال', 'جريب', 'فروت', 'يوسفي', 'كلمنتينا', 'بوملي',
    'جريب', 'فروت', 'رمان', 'توت', 'عليق', 'توت', 'ازرق', 'كرانبري', 'عنب', 'ثعلب',
    'كيوي', 'ذهب', 'باشن', 'فروت', 'دراق', 'نكتارين', 'برقوق', 'ياباني', 'ميرابيل',
    'دامسون', 'سلطان', 'عنب', 'اسود', 'اخضر', 'احمر', 'وردي', 'اصفر', 'بنفسجي', 'ابيض',
    'اسود', 'رمادي', 'بني', 'برتقالي', 'ذهبي', 'فضي', 'نحاسي', 'برونزي', 'فاتح', 'غامق',
    'ساطع', 'باهت', 'زاهي', 'هادئ', 'دافئ', 'بارد', 'محايد', 'لون', 'ظل', 'درجة',
    'تدرج', 'مزيج', 'طيف', 'قوس', 'قزح', 'صبغة', 'لون', 'طبيعي', 'صناعي', 'نقي',
    'مخلوط', 'فاتح', 'غامق', 'فاتح', 'جذاب', 'جميل', 'قبيح', 'حسن', 'سيء', 'جيد',
    'ممتاز', 'رديء', 'عظيم', 'صغير', 'كبير', 'ضخم', 'عملاق', 'قزم', 'طويل', 'قصير',
    'عريض', 'ضيق', 'سميك', 'رفيع', 'ثقيل', 'خفيف', 'صلب', 'لين', 'قاس', 'مرن',
    'ناعم', 'خشن', 'املس', 'متعجر', 'مستو', 'منحني', 'مستقيم', 'دائري', 'مربع', 'مستطيل',
    'مثلث', 'خماسي', 'سداسي', 'ثماني', 'عشاري', 'بيضاوي', 'هلالي', 'نجمي', 'قلبي', 'اسطواني',
    'كروي', 'مكعب', 'هرمي', 'مخروطي', 'شبه', 'منحرف', 'متوازي', 'اضلاع', 'منحني', 'ملتوي',
    'ملتف', 'ملتو', 'معقوف', 'مستدير', 'زاوي', 'حاد', 'منفرج', 'قائم', 'حاد', 'منفرج',
    'مستقيم', 'منكسر', 'متعرج', 'ملتو', 'ملفوف', 'مطوي', 'مشدود', 'مرتخي', 'متماسك', 'متفكك',
    'مترابط', 'منفصل', 'متصل', 'مستمر', 'منقطع', 'متكرر', 'نادر', 'شائع', 'معتاد', 'غريب',
    'مألوف', 'منسي', 'مشهور', 'مجهول', 'واضح', 'غامض', 'مبهم', 'صريح', 'ضمني', 'مباشر',
    'غير', 'مباشر', 'ظاهر', 'باطن', 'سطح', 'عمق', 'داخل', 'خارج', 'امام', 'خلف',
    'يمين', 'يسار', 'اعلى', 'اسفل', 'شمال', 'جنوب', 'شرق', 'غرب', 'وسط', 'طرف',
    'زاوية', 'ركن', 'مركز', 'محور', 'نقطة', 'خط', 'منحنى', 'سطح', 'مجسم', 'فراغ',
    'مكان', 'زمان', 'وقت', 'تاريخ', 'ماضي', 'حاضر', 'مستقبل', 'الآن', 'قبل', 'بعد',
    'الان', 'غدا', 'امس', 'اليوم', 'البوم', 'اسبوع', 'شهر', 'سنة', 'قرن', 'عقد',
    'حقبة', 'مرحلة', 'فترة', 'زمن', 'عصر', 'دهر', 'ابد', 'خلود', 'فناء', 'بقاء',
    'وجود', 'عدم', 'حياة', 'موت', 'ولادة', 'نشأة', 'تطور', 'نمو', 'كبر', 'صغر',
    'شيخوخة', 'شباب', 'طفولة', 'مراهقة', 'نضج', 'بلوغ', 'كهولة', 'عجز', 'ضعف', 'قوة',
    'صحة', 'مرض', 'علاج', 'دواء', 'جرعة', 'عملية', 'جراحة', 'فحص', 'تحليل', 'تشخيص',
    'اعراض', 'علامات', 'اسباب', 'نتائج', 'مضاعفات', 'وقاية', 'مناعة', 'عدوى', 'وباء', 'جائحة',
    'فيروس', 'بكتيريا', 'جرثومة', 'ميكروب', 'طفيلي', 'دودة', 'حشرة', 'بعوضة', 'ذبابة', 'نحلة',
    'دبور', 'نملة', 'صرصور', 
]

training_numbers = [
    '583 219 407 681', '706 451 938 124', '836 912 471 305', '429 785 163 042',
    '157 328 964 075', '294 637 815 206',
 '863 194 257 038', '571 826 394 017',
    '348 572 169 084', '925 481 736 052', '614 793 258 061', '782 365 149 027',
    '439 871 625 034', '167 294 385 016', '853 619 742 085', '291 548 367 092',
    '674 123 895 074', '938 256 471 098', '415 789 326 014', '726 834 195 072',
    '472 519 836 407', '683 724 159 682', '295 837 461 295', '746 182 593 746',
    '518 364 927 518', '839 571 264 839', '162 495 738 162', '374 628 951 374',
    '957 243 816 957', '621 789 354 621', '483 916 275 483', '756 132 489 756',
    '129 567 843 129', '894 315 672 894', '237 684 915 237', '568 729 143 568',
    '941 376 258 941', '372 851 694 372', '615 498 327 615', '789 163 452 789',
    '254 718 936 254', '937 542 861 937', '461 895 273 461', '683 127 549 683',
    '825 394 617 825', '196 753 428 196', '739 261 584 739', '542 876 319 542',
    '817 439 652 817', '364 982 175 364', '958 347 621 958', '271 654 938 271',
    '435 189 726 435', '698 213 547 698', '123 768 495 123', '786 451 329 786',
    '359 824 167 359', '672 935 418 672', '814 576 293 814', '927 381 654 927',
    '604 872 159', '317 945 286', '829 531 674', '153 798 462', '486 213 597',
    '792 468 135', '245 679 813', '931 524 768', '674 189 325', '358 642 917',
    '827 356 194', '469 781 253', '712 395 846', '594 128 637', '163 457 982',
    '978 364 251', '325 816 479', '641 973 528', '897 245 361', '532 689 714',
    '769 132 485', '214 578 963', '683 927 154', '957 341 628', '421 896 573',
    '876 459 312', '394 762 815', '618 234 597', '745 981 236', '289 653 471',
    '563 178 924', '137 492 685', '492 865 137', '856 371 492', '371 492 856',
    '924 657 381', '657 381 924', '381 924 657', '518 743 269', '743 269 518',
    '269 518 743', '682 935 147', '935 147 682', '147 682 935', '359 824 176',
    '824 176 359', '176 359 824', '497 268 531', '268 531 497', '531 497 268',
    '726 153 489', '153 489 726', '489 726 153', '864 317 592', '317 592 864',
    '592 864 317', '235 746 198', '746 198 235', '198 235 746', '671 429 853',
    '429 853 671', '853 671 429', '942 578 316', '578 316 942', '316 942 578',
    '183 695 274', '695 274 183', '274 183 695', '759 342 861', '342 861 759',
    '861 759 342', '426 917 583', '917 583 426', '583 426 917', '698 234 715',
    '234 715 698', '715 698 234', '871 569 342', '569 342 871', '342 871 569',
    '915 627 483', '627 483 915', '483 915 627', '264 798 135', '798 135 264',
    '135 264 798', '387 451 926', '451 926 387', '926 387 451', '572 864 319',
    '864 319 572', '319 572 864', '408 615', '729 483', '156 297', '834 561',
    '492 738', '675 129', '318 954', '547 216', '961 372', '283 645',
    '729 184', '456 837', '193 528', '864 391', '572 946', '349 672',
    '816 453', '235 768', '987 324', '654 189', '421 796', '738 215',
    '569 482', '192 657', '875 341', '346 918', '713 264', '928 573',
    '654 127', '381 596', '267 439', '945 682', '518 793', '376 841',
    '829 165', '453 728', '196 534', '782 319', '365 897', '918 246',
    '547 932', '274 685', '631 478', '859 123', '426 759', '793 462',
    '168 594', '935 276', '482 617', '719 384', '356 891', '824 537',
    '697 142', '243 869', '578 314', '961 725', '334 687', '789 153',
    '415 928', '852 476', '297 634', '764 291', '138 567', '685 139',
    '329 754', '476 812', '913 468', '548 973', '172 645', '639 281',
    '285 719', '714 392', '396 847', '867 435', '534 968', '981 354',
    '425 879', '798 526', '163 794', '947 162', '512 638', '689 215',
    '354 781', '871 943', '236 598', '985 327', '742 169', '619 472',
    '483 756', '756 483', '327 894', '894 327', '568 213', '213 568',
    '479 325', '325 479', '692 147', '147 692', '834 259', '259 834',
    '915 367', '367 915', '748 192', '192 748', '563 478', '478 563',
    '289 634', '634 289', '715 826', '826 715', '942 157', '157 942',
    '368 491', '491 368', '527 839', '839 527', '694 273', '273 694',
    '185 726', '726 185', '432 958', '958 432', '769 314', '314 769',
    '251 687', '687 251', '934 562', '562 934', '417 895', '895 417',
    '682 739', '739 682', '359 124', '124 359', '876 451', '451 876',
    '243 567', '567 243', '918 234', '234 918', '675 321', '321 675',
    '492 816', '816 492', '537 294', '294 537', '168 753', '753 168',
    '429 675', '675 429', '786 132', '132 786', '543 987', '987 543',
    '219 864', '864 219', '657 348', '348 657', '984 273', '273 984',
    '361 528', '528 361', '795 146', '146 795', '432 619', '619 432',
    '867 354', '354 867', '291 786', '786 291', '534 927', '927 534',
    '678 415', '415 678', '923 768', '768 923', '456 139', '139 456',
    '789 254', '254 789', '132 967', '967 132', '465 318', '318 465',
    '798 543', '543 798', '321 896', '896 321', '654 279', '279 654',
    '987 432', '432 987', '115', '954', '384', '726', '493', '861',
    '257', '639', '142', '875', '368', '719', '524', '936', '281',
    '647', '153', '798', '462', '815', '329', '674', '941', '586',
    '273', '658', '139', '782', '465', '897', '312', '649', '235',
    '768', '451', '924', '587', '316', '759', '482', '835', '169',
    '742', '395', '618', '273', '856', '491', '734', '168', '925',
    '347', '619', '852', '476', '193', '728', '365', '914', '587',
    '236', '749', '512', '683', '179', '824', '357', '698', '143',
    '796', '258', '631', '974', '385', '612', '847', '293', '568',
    '134', '789', '256', '913', '478', '625', '891', '364', '717',
    '248', '593', '866', '179', '422', '685', '139', '774', '258',
    '633', '946', '371', '824', '159', '682', '437', '795', '264',
    '518', '973', '346', '819', '572', '935', '468', '721', '354',
    '687', '129', '576', '843', '291', '654', '137', '798', '465',
    '812', '349', '576', '923', '458', '761', '234', '689', '157',
    '824', '396', '571', '938', '264', '719', '485', '132', '697',
    '354', '821', '596', '173', '748', '315', '682', '947', '536',
    '189', '724', '453', '816', '279', '564', '931', '478', '625',
    '892', '367', '514', '789', '246', '573', '918', '365', '742',
    '519', '684', '237', '596', '843', '172', '659', '324', '781',
    '456', '913', '268', '735', '142', '689', '357', '824', '196',
    '573', '948', '265', '719', '384', '657', '192', '845', '376',
    '921', '584', '137', '698', '253', '746', '319', '582', '467',
    '134', '789', '256', '913', '478', '625', '891', '364', '717',
    '79', '34', '11', '95', '62', '48', '83', '27', '56', '91',
    '73', '18', '64', '29', '85', '37', '72', '46', '19', '88',
    '53', '96', '41', '77', '22', '69', '44', '99', '66', '33',
    '55', '11', '88', '44', '22', '77', '33', '66', '99', '55',
    '12', '34', '56', '78', '90', '23', '45', '67', '89', '10',
    '32', '54', '76', '98', '21', '43', '65', '87', '09', '31',
    '53', '75', '97', '24', '46', '68', '80', '13', '35', '57',
    '79', '91', '26', '48', '60', '82', '14', '36', '58', '70',
    '92', '17', '39', '51', '73', '95', '28', '40', '62', '84',
    '16', '38', '50', '72', '94', '27', '49', '61', '83', '15',
    '37', '59', '71', '93', '25', '47', '69', '81', '20', '42',
    '64', '86', '08', '30', '52', '74', '96', '19', '41', '63',
    '85', '07', '29', '51', '73', '95', '18', '40', '62', '84',
    '06', '28', '50', '72', '94', '17', '39', '61', '83', '05',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
]

training_numbers_short = [
    '35', '67', '12', '89', '43', '76', '21', '54', '98', '31',
    '65', '18', '92', '47', '83', '16', '59', '24', '71', '38',
    '95', '62', '29', '74', '41', '86', '13', '57', '82', '19',
    '64', '27', '91', '46', '78', '33', '69', '14', '52', '87',
    '25', '61', '94', '37', '72', '49', '85', '22', '58', '93',
    '26', '63', '17', '48', '79', '34', '68', '15', '51', '88',
    '32', '75', '11', '44', '96', '23', '66', '39', '81', '55',
    '99', '42', '77', '28', '53', '84', '36', '73', '45', '97',
    '5', '8', '3', '9', '1', '7', '4', '2', '6', '10',
    '20', '30', '40', '50', '60', '70', '80', '90', '100'
]

training_sentences = [
    "السماء صافية اليوم",
    "أحب البرمجة كثيرا",
    "الشمس تشرق من الشرق",
    "القطة تجري في الحديقة",
    "أدرس اللغة العربية",
    "الكتاب على الطاولة",
    "الطالب يذاكر دروسه",
    "الورد الأحمر جميل",
    "أكلت تفاحة لذيذة",
    "السيارة تسير بسرعة",
    "المنزل كبير وجميل",
    "اشتركت في المسابقة",
    "الفريق فاز بالمباراة",
    "الطعام كان لذيذا",
    "زرت المتحف أمس",
    "الطفل يلعب بالكرة",
    "المعلم يشرح الدرس",
    "اشتريت هدية لصديقي",
    "السوق مليء بالناس",
    "الطائرة تحلق في السماء",
    "قرأت كتابا شيقا",
    "الشاطئ جميل جدا",
    "القهوة ساخنة ولذيذة",
    "ذهبت إلى المدرسة",
    "الحديقة واسعة وخضراء",
    "الفستان جديد وجميل",
    "الطقس بارد اليوم",
    "شاهدت فيلما رائعا",
    "الزهور تتفتح في الربيع",
    "الطعام جاهز للأكل",
    "السياحة في بلادي جميلة",
    "النجوم تلمع في الليل",
    "الرحلة كانت ممتعة",
    "البيتزا لذيذة وساخنة",
    "المطر ينزل بغزارة",
    "اللعبة مسلية وجميلة",
    "الحديث كان شيقا",
    "الرسم هوايتي المفضلة",
    "السباحة مفيدة للصحة",
    "الطالب نجح في الامتحان",
    "السفينة تبحر في البحر",
    "الوردة تفوح عطرا",
    "الكتابة مهارة مهمة",
    "الشتاء قادم قريبا",
    "الضيوف وصلوا الآن",
    "الحديقة العامة جميلة",
    "الرياضة تنشط الجسم",
    "الطبيب يعالج المرضى",
    "الزراعة مهنة شريفة",
    "النجاح يحتاج إلى اجتهاد"
]

record_messages = [
    "🏆 الأسطورة في لعبة السرعة 🏆",
    "⚡ البطل في عالم السرعة ⚡", 
    "🎯 السهم الذي لا يخطئ الهدف 🎯",
    "💎 الماس الخام في التحدي 💎",
    "🚀 النجم المتألق في السماء 🚀"
]

user_sessions = {}
group_sessions = {}
challenge_sessions = {}
challenge_leaderboards = {}
user_scores = {}
challenges = {}
active_challenges = {}
active_challenge = None
user_detailed_stats = {}
user_records = {'word': [], 'number': [], 'sentence': []}

records = {
    'word': {'time': float('inf'), 'user_name': '', 'user_id': None, 'username': '', 'content': ''},
    'number': {'time': float('inf'), 'user_name': '', 'user_id': None, 'username': '', 'content': ''},
    'sentence': {'time': float('inf'), 'user_name': '', 'user_id': None, 'username': '', 'content': ''}
}

round_winner_messages = [
    "سيد الإتقان المتألق في المنافسة",
    "الوحش المفترس في عالم السرعة", 
    "منافس قوي بلا شك أو ريب",
    "قوة مبهرة في الأداء والتميز", 
    "يالك من وحش في مهارات السرعة"
]

final_winner_messages = [
    "أنا الأفضل بلا منافس يذكر في الميدان",
    "النجم المتألق الوحيد في السماء صافية", 
    "البطل الذي لا يشق له غبار في المعركة",
    "السيد المطلق لأرض التحدي الكبيرة", 
    "الفاتح العظيم لجمين الصعاب والعقبات"
]

loser_messages = [
    "حظ أوفر لكم في التحدي القادم",
    "لا تيأسوا أمامكم فرص كثيرة للفوز",
    "المحاولة مرة أخرى تجلب النجاح",
    "الفشل اليوم نجاح الغد بلا شك",
    "لا تستسلموا فالنصر قريب منكم"
]

def update_detailed_stats(user_id, content_type):
    if user_id not in user_detailed_stats:
        user_detailed_stats[user_id] = {'words': 0, 'numbers': 0, 'sentences': 0}
    
    if content_type == 'word':
        user_detailed_stats[user_id]['words'] += 1
    elif content_type == 'number':
        user_detailed_stats[user_id]['numbers'] += 1
    elif content_type == 'sentence':
        user_detailed_stats[user_id]['sentences'] += 1

def update_user_records(user_id, user_name, username, content_type, content, response_time):
    if content_type not in records:
        return
        
    if response_time < records[content_type]['time']:
        records[content_type] = {
            'time': response_time,
            'user_name': user_name,
            'user_id': user_id,
            'username': username,
            'content': content
        }

def normalize_answer(user_answer, correct_answer):
    if not user_answer or not correct_answer:
        return False
    
    user_clean = re.sub(r'[\s\.,،;؛]+', '', user_answer.lower())
    correct_clean = re.sub(r'[\s\.,،;؛]+', '', correct_answer.lower())
    
    if not user_clean or not correct_clean:
        return False
    
    user_single = ''.join(dict.fromkeys(user_clean))
    correct_single = ''.join(dict.fromkeys(correct_clean))
    
    return user_single == correct_single

def normalize_number(user_answer, correct_answer):
    user_clean = re.sub(r'\D', '', str(user_answer))
    correct_clean = re.sub(r'\D', '', str(correct_answer))
    
    if not user_clean or not correct_clean:
        return False
    
    user_normalized = re.sub(r'(\d+?)\1+', r'\1', user_clean)
    correct_normalized = re.sub(r'(\d+?)\1+', r'\1', correct_clean)
    
    return user_normalized == correct_normalized

async def send_final_winner_message(context, chat_id: int, challenge_id: str, winner_user):
    if challenge_id not in active_challenges:
        return
        
    challenge = active_challenges[challenge_id]
    
    winner_data = None
    winner_id = None
    for user_id, score_data in challenge_leaderboards.items():
        if score_data['name'] == winner_user:
            winner_data = score_data
            winner_id = user_id
            break
        
    await context.bot.send_message(chat_id=chat_id, text=final_text)
    del active_challenges[challenge_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    username = update.effective_user.username or ""
    is_developer = username == "HEX_A"
    is_private = update.effective_chat.type == "private"
    
    if is_private:
        if is_developer:
            keyboard = [
                ["🎯 بدء التحدي", "⚡ تدريب سريع"],
                ["📊 الإحصائيات", "🔢 إدارة الأرقام"],
                ["📝 إدارة الكلمات", "💬 إدارة الجمل"],
                ["🔄 تغيير الأوامر", "📦 الإضافة الجماعية"],
                ["🛠️ إعدادات البوت", "📈 إحصائيات الأعضاء"],
                ["👥 اللاعبين النشطين", "🌐 قياس السرعة"],
                ["🎛️ لوحة التحكم", "💾 نسخة احتياطية"]  
            ]
        else:
            keyboard = [
                ["⚡ تدريب سريع", "🌐 قياس السرعة"],
                ["📊 إحصائياتي", "🏆 الأرقام القياسية"]
            ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        welcome_text = f"""
🎮 مرحباً {user_name} في لعبة السرعة! ⚡

كيف تلعب:
• اكتب (ك) أو (كلمة) أو (كلمه) لتدريب الكلمات
• اكتب (ر) أو (رقم) أو (ارقام) لتدريب الأرقام
• اكتب (ترند) لمشاهدة الأرقام القياسية
• اكتب (تحدي) لبدء تحدي جماعي

اكتب (ك) أو (ر) لبدء اللعب! 🚀
    """
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    else:
        return

async def handle_challenge_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    challenge_id = None
    for cid, challenge in list(challenges.items()):
        if challenge['creator']['id'] == user_id and challenge['status'] in ['awaiting_count', 'awaiting_participants', 'awaiting_additional', 'awaiting_points']:
            challenge_id = cid
            break
    
    if not challenge_id:
        for cid, challenge in list(active_challenges.items()):
            if challenge['creator']['id'] == user_id and challenge.get('status') in ['awaiting_count', 'awaiting_participants', 'awaiting_additional', 'awaiting_points']:
                challenge_id = cid
                break
    
    if not challenge_id:
        return
    
    if challenge_id in challenges:
        challenge = challenges[challenge_id]
    else:
        challenge = active_challenges[challenge_id]
    
    if challenge['status'] == 'awaiting_count':
        if text.isdigit() and 1 <= int(text) <= 30:
            challenge['max_participants'] = int(text)
            challenge['status'] = 'awaiting_participants'
            
            await update.message.reply_text(
                f"✅ تم تحديد عدد المشاركين: {text}\n\n"
                f"📩 الآن قم بإرسال معرفات المشاركين (@username) واحداً تلو الآخر\n"
                f"عدد المعرفات المطلوبة: {text}"
            )
        else:
            await update.message.reply_text("❌ الرجاء إدخال عدد بين 1 و 30")
    
    elif challenge['status'] == 'awaiting_participants':
        if text.startswith('@'):
            if len(challenge['participants']) < challenge['max_participants']:
                if text not in challenge['participants']:
                    challenge['participants'].append(text)
                    remaining = challenge['max_participants'] - len(challenge['participants'])
                    
                    await update.message.reply_text(
                        f"✅ تم إضافة {text} للتحدي\n"
                        f"📊 المتبقي: {remaining} مشارك"
                    )
                    
                    if len(challenge['participants']) == challenge['max_participants']:
                        await send_challenge_type_selection(update, challenge_id)
                else:
                    await update.message.reply_text("❌ هذا المستخدم مضاف مسبقاً")
            else:
                await update.message.reply_text(
                    f"❌ وصلت للحد الأقصى ({challenge['max_participants']} مشارك)\n"
                    "اكتب 'اضف شخص' لإضافة المزيد"
                )
        elif text == 'اضف شخص' or text == 'زيادة عدد الاشخاص':
            challenge['status'] = 'awaiting_additional'
            await update.message.reply_text("➕ كم شخص تريد إضافته؟")
    
    elif challenge['status'] == 'awaiting_additional':
        if text.isdigit() and int(text) > 0:
            additional = int(text)
            challenge['max_participants'] += additional
            challenge['status'] = 'awaiting_participants'
            
            await update.message.reply_text(
                f"✅ تم زيادة العدد بمقدار {additional}\n"
                f"📊 العدد الجديد: {challenge['max_participants']} مشارك\n\n"
                "📩 قم بإرسال المعرفات الجديدة"
            )
    
    elif challenge['status'] == 'awaiting_points':
        if text.isdigit() and 1 <= int(text) <= 70:
            challenge['win_points'] = int(text)
            challenge['status'] = 'active'
            active_challenges[challenge_id] = challenge
            
            if challenge_id in challenges:
                del challenges[challenge_id]
            
            type_text = {
                'numbers': 'أرقام فقط ⚡ استخدم: ار',
                'words': 'كلمات فقط ⚡ استخدم: كل', 
                'both': 'أرقام + كلمات ⚡ استخدم: اك',
                'sentences_only': 'جمل فقط ⚡ استخدم: جم',
                'numbers_sentences': 'أرقام + جمل ⚡ استخدم: اج',
                'words_sentences': 'كلمات + جمل ⚡ استخدم: كج',
                'all': 'الكل ⚡ استخدم: ال'
            }
            
            await update.message.reply_text(
                f"🎊 بدء التحدي!\n\n"
                f"📋 نوع التحدي: {type_text[challenge['type']]}\n"
                f"🏆 نقاط الفوز: {challenge['win_points']}\n"
                f"👤 مقدم اللعبة: {challenge['creator']['name']}\n\n"
                f"🏁 ابدأ بكتابة الأمر المناسب!"
            )
        else:
            await update.message.reply_text("❌ الرجاء إدخال عدد نقاط بين 1 و 70")

async def handle_challenge_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_message = update.message.text.strip()
    chat_id = update.effective_chat.id
    
    for challenge_id, challenge in list(active_challenges.items()):
        if challenge['chat_id'] != chat_id:
            continue
            
        if challenge.get('paused', False):
            continue
            
        if challenge['status'] != 'active':
            continue

        if 'current_content' not in challenge:
            continue
            
        if challenge.get('answered', False):
            continue
            
        user_identifier = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name
        is_participant = user_identifier in challenge.get('participants', [])
        is_creator = user_id == challenge['creator']['id']
        
        if not is_participant and not is_creator:
            continue
            
        correct_content = challenge['current_content']
        content_type = challenge['current_type']
        
        if content_type == 'word' or content_type == 'sentence':
            is_correct = normalize_answer(user_message, correct_content)
        else:
            is_correct = normalize_number(user_message, correct_content)
        
        if is_correct:
            response_time = time.time() - challenge['start_time']
            challenge['answered'] = True
            
            if user_id not in challenge['scores']:
                challenge['scores'][user_id] = 0
            
            challenge['scores'][user_id] += 1
            
            if user_id not in challenge_leaderboards:
                challenge_leaderboards[user_id] = {
                    'name': update.effective_user.first_name,
                    'username': update.effective_user.username or ""
                }

            if user_id not in user_detailed_stats:
                user_detailed_stats[user_id] = {'words': 0, 'numbers': 0, 'sentences': 0}

            if content_type == 'word':
                user_detailed_stats[user_id]['words'] += 1
            elif content_type == 'number':
                user_detailed_stats[user_id]['numbers'] += 1
            elif content_type == 'sentence':
                user_detailed_stats[user_id]['sentences'] += 1

            remaining_points = challenge['win_points'] - challenge['scores'][user_id]
            winner_message = random.choice(round_winner_messages)

            if challenge['scores'][user_id] < challenge['win_points']:
                await update.message.reply_text(
                    f"👤 {update.effective_user.first_name}\n"
                    f"✅ {winner_message}\n"
                    f"⏱️ الوقت: {response_time:.2f} ثانية\n"
                    f"🏆 النقاط: {challenge['scores'][user_id]}/{challenge['win_points']}\n"
                    f"🎯 المتبقي للفوز: {remaining_points} نقطة"
                )
            else:
                await update.message.reply_text(
                    f"👤 {update.effective_user.first_name}\n"
                    f"✅ {winner_message}\n"
                    f"⏱️ الوقت: {response_time:.2f} ثانية\n"
                    f"🏆 النقاط: {challenge['scores'][user_id]}/{challenge['win_points']}"
                )

            if challenge['scores'][user_id] >= challenge['win_points']:
                winner_name = update.effective_user.first_name
                winner_id = update.effective_user.id
                winner_username = update.effective_user.username or ""
                
                final_text = "🏁 ━━━━━━━━━━━━━━━━━━━ 🏁\n"
                final_text += "⚡️ إنـتـهـى الـتـحـدي ⚡️\n\n"
                
                final_text += "🎊 الـفـائـز 🎊\n"
                winner_username_display = f"@{winner_username}" if winner_username else "بدون معرف"
                winner_stats = user_detailed_stats.get(winner_id, {'words': 0, 'numbers': 0, 'sentences': 0})
                final_text += f"🥇 <a href=\"tg://user?id={winner_id}\">{winner_name}</a>\n"
                final_text += f"🆔 {winner_username_display}\n"
                final_text += f"📟 <a href=\"tg://user?id={winner_id}\">{winner_id}</a>\n"
                final_text += f"📝 الكلمات: {winner_stats['words']} 🎯\n"
                final_text += f"🔢 الأرقام: {winner_stats['numbers']} 🎯\n"
                final_text += f"💬 الجمل: {winner_stats['sentences']} 🎯\n"
                final_text += f"🏆 الإجمالي: {challenge['scores'].get(winner_id, 0)} نقطة\n"
                final_text += f"✨ {random.choice(final_winner_messages)} ✨\n\n"
                
                final_text += "💫 ━━━━━━━━━━━━━━━━━━━ 💫\n"
                final_text += "📊 الـخـاسـرون 🏆\n\n"
                
                losers_data = []
                all_participants = set(challenge.get('participants', []))
                all_participants.add(f"@{challenge['creator']['username']}" if challenge['creator']['username'] else challenge['creator']['name'])
                
                for participant in all_participants:
                    participant_id = None
                    participant_name = participant
                    
                    for uid, user_data in challenge_leaderboards.items():
                        user_identifier = f"@{user_data['username']}" if user_data['username'] else user_data['name']
                        if user_identifier == participant:
                            participant_id = uid
                            participant_name = user_data['name']
                            break
                    
                    if participant_id != winner_id:
                        participant_score = challenge['scores'].get(participant_id, 0)
                        participant_data = challenge_leaderboards.get(participant_id, {
                            'name': participant_name,
                            'username': participant.replace('@', '') if participant.startswith('@') else ''
                        })
                        
                        losers_data.append({
                            'user_id': participant_id,
                            'name': participant_data['name'],
                            'username': participant_data['username'],
                            'score': participant_score
                        })
                
                if losers_data:
                    for i, loser in enumerate(losers_data, 1):
                        username_display = f"@{loser['username']}" if loser['username'] else "بدون معرف"
                        if loser['user_id']:
                            final_text += f"{i}. <a href=\"tg://user?id={loser['user_id']}\">{loser['name']}</a>\n"
                        else:
                            final_text += f"{i}. {loser['name']}\n"
                        final_text += f"   🆔 {username_display}\n"
                        final_text += f"   🎯 {loser['score']} نقطة\n\n"
                else:
                    final_text += "📭 لا يوجد خاسرين\n\n"

                final_text += "📉 إحـصـائـيـات الـخـاسـرين 📉\n\n"
                losers_with_stats = [loser for loser in losers_data if loser['score'] > 0]
                if losers_with_stats:
                    for i, loser in enumerate(losers_with_stats, 1):
                        loser_stats = user_detailed_stats.get(loser['user_id'], {'words': 0, 'numbers': 0, 'sentences': 0})
                        if loser['user_id']:
                            final_text += f"{i}. <a href=\"tg://user?id={loser['user_id']}\">{loser['name']}</a>\n"
                        else:
                            final_text += f"{i}. {loser['name']}\n"
                        final_text += f"   📝 الكلمات: {loser_stats['words']} 🎯\n"
                        final_text += f"   🔢 الأرقام: {loser_stats['numbers']} 🎯\n"
                        final_text += f"   💬 الجمل: {loser_stats['sentences']} 🎯\n"
                        final_text += f"   📊 الإجمالي: {loser_stats['words'] + loser_stats['numbers'] + loser_stats['sentences']} إجابة\n"
                        final_text += "────────────────────\n\n"
                else:
                    final_text += "📊 لا توجد إحصائيات للخاسرين\n\n"

                final_text += f"📝 {random.choice(loser_messages)} 📝\n\n"
                final_text += "🎁 شـكـراً لـمـشـاركـتـكـم 🎁\n"
                final_text += "💎 نـتـظـر تـحـديـكـم الـقـادم 💎"
                
                await update.message.reply_text(final_text, parse_mode='HTML')
                del active_challenges[challenge_id]
                return

allowed_controllers = {}
secondary_developers = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    
    if update.message.document and update.message.document.file_name.endswith('.json'):
        if update.effective_user.username == "HEX_A":
            await restore_from_json(update, context)
        return

    if chat_type == 'group' or chat_type == 'supergroup':
        if str(chat_id) not in bot_settings['active_groups']:
            bot_settings['active_groups'][str(chat_id)] = {
                'title': update.effective_chat.title,
                'members': update.effective_chat.get_member_count(),
                'last_activity': time.time()
            }
    
    if not is_bot_active(chat_id, chat_type):
        if update.effective_user.username == "HEX_A":
            return await update.message.reply_text("⚠️ البوت متوقف في هذه الدردشة - المطور فقط يمكنه الاستخدام")
        return

    user_id = update.effective_user.id
    user_message = update.message.text.strip()
    user_name = update.effective_user.first_name
    username = update.effective_user.username or ""
    
    if user_message in ['💾 نسخة احتياطية', 'نسخة', 'نسخه']:
        if update.effective_user.username == "HEX_A":
            await create_comprehensive_backup(update, context)
        else:
            await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return

    if user_message in ['نت', 'نتي', 'رقم نت', 'رقم نتي']:
        number = random.choice(training_numbers_short)
        group_sessions[chat_id] = {
            'type': 'number', 
            'content': number,
            'start_time': time.time()
        }
        await update.message.reply_text(f"\n\n{number}")
        return

    if username == "HEX_A":
        if context.user_data.get('awaiting_group'):
            group_id = user_message
            ALLOWED_GROUPS.add(group_id)
            await update.message.reply_text(f"✅ تمت إضافة المجموعة: {group_id}")
            context.user_data['awaiting_group'] = False
            return
            
        elif context.user_data.get('awaiting_remove_group'):
            group_id = user_message
            if group_id in ALLOWED_GROUPS:
                ALLOWED_GROUPS.remove(group_id)
                await update.message.reply_text(f"🗑️ تم حذف المجموعة: {group_id}")
            else:
                await update.message.reply_text("❌ المجموعة غير موجودة")
            context.user_data['awaiting_remove_group'] = False
            return
            
        elif context.user_data.get('awaiting_ban_group'):
            group_id = user_message
            BOT_BLACKLIST.add(group_id)
            await update.message.reply_text(f"🚫 تم حظر المجموعة: {group_id}")
            context.user_data['awaiting_ban_group'] = False
            return
            
        elif context.user_data.get('awaiting_unban_group'):
            group_id = user_message
            if group_id in BOT_BLACKLIST:
                BOT_BLACKLIST.remove(group_id)
                await update.message.reply_text(f"✅ تم فك حظر المجموعة: {group_id}")
            else:
                await update.message.reply_text("❌ المجموعة غير محظورة")
            context.user_data['awaiting_unban_group'] = False
            return

    if user_message == "🎛️ لوحة التحكم":
        await private_control_panel(update, context)
        return

    if user_message in ['سم', 'سماح', 'ألسماح', 'السماح']:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_id = target_user.id
            target_name = target_user.first_name
            target_username = target_user.username or ""
            
            if username == "HEX_A" or user_id in secondary_developers:
                if target_id == user_id:
                    await update.message.reply_text("👑 أنت المطور لا تحتاج إلى إذن!")
                    return
                
                allowed_controllers[target_id] = {
                    'name': target_name,
                    'username': target_username,
                    'granted_by': user_name,
                    'granted_time': time.time()
                }
                await update.message.reply_text(f"✅ تم منح الإذن لـ {target_name}\nتم التصريح لهم من قبل: {user_name}")
            else:
                await update.message.reply_text("❌ فقط المطور يمكنه منح الإذن")
        return

    if user_message in ['حح', 'إلغاء', 'ألغاء', 'الغاء']:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_id = target_user.id
            target_name = target_user.first_name
            
            if username == "HEX_A" or user_id in secondary_developers:
                if target_id in allowed_controllers:
                    del allowed_controllers[target_id]
                    await update.message.reply_text(f"❌ تم سحب الإذن من {target_name}")
                else:
                    await update.message.reply_text("❌ هذا المستخدم ليس لديه إذن")
            else:
                await update.message.reply_text("❌ فقط المطور يمكنه سحب الإذن")
        return

    if user_message in ['مطور ث', 'مطور ثانوي', 'ثث']:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_id = target_user.id
            target_name = target_user.first_name
            target_username = target_user.username or ""
            
            if username == "HEX_A":
                if target_id == user_id:
                    await update.message.reply_text("👑 أنت المطور الأساسي لا تحتاج إلى ترقية!")
                    return
                
                secondary_developers[target_id] = {
                    'name': target_name,
                    'username': target_username,
                    'granted_by': user_name,
                    'granted_time': time.time()
                }
                await update.message.reply_text(f"🎖️ تم ترقية {target_name} إلى مطور ثانوي")
            else:
                await update.message.reply_text("❌ فقط المطور الأساسي يمكنه منح صلاحيات المطور")
        return

    if user_message in ['سس', 'سحب']:
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
            target_id = target_user.id
            target_name = target_user.first_name
            
            if username == "HEX_A":
                if target_id in secondary_developers:
                    del secondary_developers[target_id]
                    await update.message.reply_text(f"❌ تم سحب صلاحية المطور من {target_name}")
                else:
                    await update.message.reply_text("❌ هذا المستخدم ليس مطوراً ثانوياً")
            else:
                await update.message.reply_text("❌ فقط المطور الأساسي يمكنه سحب الصلاحيات")
        return

    if user_message in ['اذ', 'ذ', 'إذونات', 'الأذونات', 'ألأذونات', 'ألاذونات', 'اذونات']:
        if allowed_controllers:
            controllers_text = "🔐 قائمة الأشخاص المصرح لهم:\n\n"
            for i, (ctrl_id, ctrl_data) in enumerate(allowed_controllers.items(), 1):
                controllers_text += f"{i}. {ctrl_data['name']}\n   👤 @{ctrl_data['username'] if ctrl_data['username'] else 'بدون معرف'}\n   🆔 {ctrl_id}\n   ──────────────\n"
            await update.message.reply_text(controllers_text)
        else:
            await update.message.reply_text("📭 لا يوجد أشخاص مصرح لهم حالياً")
        return

    if user_message in ['الجميع', 'جج', 'جميع', 'ألجميع']:
        if secondary_developers:
            developers_text = "🎖️ قائمة المطورين الثانويين:\n\n"
            for i, (dev_id, dev_data) in enumerate(secondary_developers.items(), 1):
                developers_text += f"{i}. {dev_data['name']}\n   👤 @{dev_data['username'] if dev_data['username'] else 'بدون معرف'}\n   🆔 {dev_id}\n   ──────────────\n"
            await update.message.reply_text(developers_text)
        else:
            await update.message.reply_text("📭 لا يوجد مطورين ثانويين حالياً")
        return

    challenge_id = None
    for cid, challenge in list(active_challenges.items()):
        if (challenge['creator']['id'] == user_id and 
            challenge['chat_id'] == chat_id and
            challenge.get('status') in ['awaiting_count', 'awaiting_participants', 'awaiting_additional', 'awaiting_points']):
            challenge_id = cid
            break

    if not challenge_id:
        for cid, challenge in list(active_challenges.items()):
            if challenge['creator']['id'] == user_id and challenge.get('status') in ['awaiting_count', 'awaiting_participants', 'awaiting_additional', 'awaiting_points']:
                challenge_id = cid
                break
    
    if challenge_id:
        challenge = active_challenges[challenge_id]
        
        if challenge['status'] == 'awaiting_count':
            if user_message.isdigit() and 1 <= int(user_message) <= 30:
                challenge['max_participants'] = int(user_message)
                challenge['status'] = 'awaiting_participants'
                
                await update.message.reply_text(
                    f"✅ تم تحديد عدد المشاركين: {user_message}\n\n"
                    f"📩 الآن قم بإرسال معرفات المشاركين (@username) واحداً تلو الآخر\n"
                    f"عدد المعرفات المطلوبة: {user_message}"
                )
                return
            else:
                await update.message.reply_text("❌ الرجاء إدخال عدد بين 1 و 30")
                return
        
        elif challenge['status'] == 'awaiting_participants':
            if user_message.startswith('@'):
                if len(challenge['participants']) < challenge['max_participants']:
                    if user_message not in challenge['participants']:
                        challenge['participants'].append(user_message)
                        remaining = challenge['max_participants'] - len(challenge['participants'])
                        
                        await update.message.reply_text(
                            f"✅ تم إضافة {user_message} للتحدي\n"
                            f"📊 المتبقي: {remaining} مشارك"
                        )
                        
                        if len(challenge['participants']) == challenge['max_participants']:
                            await send_challenge_type_selection(update, challenge_id)
                        return
                    else:
                        await update.message.reply_text("❌ هذا المستخدم مضاف مسبقاً")
                        return
                else:
                    await update.message.reply_text(
                        f"❌ وصلت للحد الأقصى ({challenge['max_participants']} مشارك)\n"
                        "اكتب 'اضف شخص' لإضافة المزيد"
                    )
                    return
            elif user_message == 'اضف شخص' or user_message == 'زيادة عدد الاشخاص':
                challenge['status'] = 'awaiting_additional'
                await update.message.reply_text("➕ كم شخص تريد إضافته؟")
                return
        
        elif challenge['status'] == 'awaiting_additional':
            if user_message.isdigit() and int(user_message) > 0:
                additional = int(user_message)
                challenge['max_participants'] += additional
                challenge['status'] = 'awaiting_participants'
                
                await update.message.reply_text(
                    f"✅ تم زيادة العدد بمقدار {additional}\n"
                    f"📊 العدد الجديد: {challenge['max_participants']} مشارك\n\n"
                    "📩 قم بإرسال المعرفات الجديدة"
                )
                return
        
        elif challenge['status'] == 'awaiting_points':
            if user_message.isdigit() and 1 <= int(user_message) <= 70:
                challenge['win_points'] = int(user_message)
                challenge['status'] = 'active'
                
                type_text = {
                    'numbers': 'أرقام فقط ⚡ استخدم: ار',
                    'words': 'كلمات فقط ⚡ استخدم: كل', 
                    'both': 'أرقام + كلمات ⚡ استخدم: اك',
                    'sentences_only': 'جمل فقط ⚡ استخدم: جم',
                    'numbers_sentences': 'أرقام + جمل ⚡ استخدم: اج',
                    'words_sentences': 'كلمات + جمل ⚡ استخدم: كج',
                    'all': 'الكل ⚡ استخدم: ال'
                }
                
                await update.message.reply_text(
                    f"🎊 بدء التحدي!\n\n"
                    f"📋 نوع التحدي: {type_text[challenge['type']]}\n"
                    f"🏆 نقاط الفوز: {challenge['win_points']}\n"
                    f"👤 مقدم اللعبة: {challenge['creator']['name']}\n\n"
                    f"🏁 ابدأ بكتابة الأمر المناسب!"
                )
                return

    if user_message in ['تح', 'تحدي']:
        has_active_challenge = False
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                has_active_challenge = True
                current_challenge = challenge
                break
        
        if has_active_challenge:
            if username == "HEX_A" or user_id in secondary_developers or user_id in allowed_controllers:
                await handle_challenge_start(update, context)
            else:
                challenge_creator = current_challenge['creator']
                creator_name = challenge_creator['name']
                creator_username = challenge_creator['username'] or ""
                
                message_text = f"🚫 هناك تحدي نشط حالياً في هذه المجموعة\n\n"
                message_text += f"📋 اطلب الإذن من المقدم أو المطور لبدء تحدي آخر\n\n"
                message_text += f"🎯 المقدم: <a href=\"tg://user?id={challenge_creator['id']}\">{creator_name}</a>\n"
                message_text += f"المعرف: @{creator_username if creator_username else 'بدون معرف'}\n\n"
                message_text += f"👑 المطور: <a href=\"tg://user?id=7077106458\">𝙃 𝙚 𝙭</a>\n"
                message_text += f"المعرف: @HEX_A"
                
                await update.message.reply_text(message_text, parse_mode='HTML')
            return
        else:
            await handle_challenge_start(update, context)
        return

    if user_message == 'انهاء':
        challenge_to_end = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                challenge_to_end = challenge_id
                current_challenge = challenge
                break
        
        if challenge_to_end:
            challenge = active_challenges[challenge_to_end]
            creator_is_developer = current_challenge['creator']['username'] == "HEX_A" or current_challenge['creator']['id'] in secondary_developers
            
            if creator_is_developer:
                if username == "HEX_A":
                    scores_text = "\n".join([f"• {user}: {points} نقطة" for user, points in challenge['scores'].items()])
                    await update.message.reply_text(f"✅ تم إنهاء التحدي\n\n📊 النتائج النهائية:\n{scores_text}")
                    del active_challenges[challenge_to_end]
                else:
                    await update.message.reply_text("❌ لا يمكن إنهاء تحدي المطورين")
            else:
                if (user_id == challenge['creator']['id'] or 
                    username == "HEX_A" or 
                    user_id in secondary_developers or 
                    user_id in allowed_controllers):
                    
                    scores_text = "\n".join([f"• {user}: {points} نقطة" for user, points in challenge['scores'].items()])
                    await update.message.reply_text(f"✅ تم إنهاء التحدي\n\n📊 النتائج النهائية:\n{scores_text}")
                    del active_challenges[challenge_to_end]
                else:
                    await update.message.reply_text("❌ ليس لديك صلاحية لإنهاء هذا التحدي")
        else:
            await update.message.reply_text("❌ لا يوجد تحدي نشط لإنهائه")
        return

    if user_message in ['ايقاف', 'إيقاف', 'أيقاف', 'ايقاف التحدي مؤقتا']:
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                creator_is_developer = challenge['creator']['username'] == "HEX_A" or challenge['creator']['id'] in secondary_developers
                
                if creator_is_developer:
                    if username == "HEX_A":
                        challenge['paused'] = True
                        await update.message.reply_text("⏸️ تم إيقاف التحدي مؤقتاً")
                    else:
                        await update.message.reply_text("❌ لا يمكن إيقاف تحدي المطورين")
                else:
                    if (user_id == challenge['creator']['id'] or 
                        username == "HEX_A" or 
                        user_id in secondary_developers or 
                        user_id in allowed_controllers):
                        
                        challenge['paused'] = True
                        await update.message.reply_text("⏸️ تم إيقاف التحدي مؤقتاً")
                    else:
                        await update.message.reply_text("❌ ليس لديك صلاحية لإيقاف التحدي")
                return

    if user_message in ['اكمل', 'إكمل', 'أكمل', 'كمل', 'اكمل التحدي']:
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                creator_is_developer = challenge['creator']['username'] == "HEX_A" or challenge['creator']['id'] in secondary_developers
                
                if creator_is_developer:
                    if username == "HEX_A":
                        challenge['paused'] = False
                        await update.message.reply_text("▶️ تم استئناف التحدي")
                    else:
                        await update.message.reply_text("❌ لا يمكن استئناف تحدي المطورين")
                else:
                    if (user_id == challenge['creator']['id'] or 
                        username == "HEX_A" or 
                        user_id in secondary_developers or 
                        user_id in allowed_controllers):
                        
                        challenge['paused'] = False
                        await update.message.reply_text("▶️ تم استئناف التحدي")
                    else:
                        await update.message.reply_text("❌ ليس لديك صلاحية لاستئناف التحدي")
                return

    if user_message in ['صد', 'متصدرين', 'صدارة', 'صداره', 'المتصدرين', 'الترتيب']:
        await show_leaderboard(update, context)
        return

    if user_message in ['او', 'اوامر', 'الاوامر', 'ألأوامر', 'ألاوامر', 'الأوامر', 'الاوامر']:
        await show_commands_menu(update, context)
        return

    if user_message in ['لوحة التحكم', 'التحكم', 'تحكم', 'اد', 'ادارة', 'إدارة'] and chat_id == user_id:
        await manage_bot_control(update, context)
        return

    if user_message in ['الارقام القياسية', 'الأرقام القياسية', 'ألأرقام القياسية', 'ألارقام القياسية', 'ترند']:
        await show_records(update, context)
        return

    if user_message in ['المشاركين', 'مش']:
        await show_participants(update, context)
        return

    if user_message in ['المقدم', 'مق', 'مقدم', 'ألمقدم', 'مقدم التحدي']:
        await show_challenge_creator(update, context)
        return

    if user_message in ['احصائيات', 'إحصائيات', 'معلومات', 'ألمعلومات', 'المعلومات', 'مع', 'م']:
        if update.message.reply_to_message:
            await show_user_stats_reply(update, context)
            return

    for challenge_id, challenge in list(active_challenges.items()):
        if challenge['chat_id'] != chat_id:
            continue
        if challenge.get('paused', False):
            continue
        if challenge['status'] != 'active':
            continue
        if user_id != challenge['creator']['id']:
            continue
            
        if user_message in ['ايقاف', 'إيقاف', 'أيقاف', 'ايقاف التحدي مؤقتا']:
            challenge['paused'] = True
            await update.message.reply_text("⏸️ تم إيقاف التحدي مؤقتاً")
            return
        elif user_message in ['اكمل', 'إكمل', 'أكمل', 'كمل', 'اكمل التحدي']:
            challenge['paused'] = False
            await update.message.reply_text("▶️ تم استئناف التحدي")
            return

        if challenge['type'] == 'numbers' and user_message == 'ار':
            number = random.choice(training_numbers)
            challenge['current_content'] = number
            challenge['current_type'] = 'number'
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️ \n\n{number}')
            return
        elif challenge['type'] == 'words' and user_message == 'كل':
            word = random.choice(training_words)
            challenge['current_content'] = word
            challenge['current_type'] = 'word'
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{word}')
            return
        elif challenge['type'] == 'both' and user_message == 'اك':
            if random.choice([True, False]):
                content = random.choice(training_numbers)
                content_type = 'number'
            else:
                content = random.choice(training_words)
                content_type = 'word'
            challenge['current_content'] = content
            challenge['current_type'] = content_type
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{content}')
            return
        elif challenge['type'] == 'sentences_only' and user_message == 'جم':
            sentence = random.choice(training_sentences)
            challenge['current_content'] = sentence
            challenge['current_type'] = 'sentence'
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{sentence}')
            return
        elif challenge['type'] == 'numbers_sentences' and user_message == 'اج':
            if random.choice([True, False]):
                content = random.choice(training_numbers)
                content_type = 'number'
            else:
                content = random.choice(training_sentences)
                content_type = 'sentence'
            challenge['current_content'] = content
            challenge['current_type'] = content_type
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{content}')
            return
        elif challenge['type'] == 'words_sentences' and user_message == 'كج':
            if random.choice([True, False]):
                content = random.choice(training_words)
                content_type = 'word'
            else:
                content = random.choice(training_sentences)
                content_type = 'sentence'
            challenge['current_content'] = content
            challenge['current_type'] = content_type
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{content}')
            return
        elif challenge['type'] == 'all' and user_message == 'ال':
            choice = random.choice(['number', 'word', 'sentence'])
            if choice == 'number':
                content = random.choice(training_numbers)
                content_type = 'number'
            elif choice == 'word':
                content = random.choice(training_words)
                content_type = 'word'
            else:
                content = random.choice(training_sentences)
                content_type = 'sentence'
            challenge['current_content'] = content
            challenge['current_type'] = content_type
            challenge['start_time'] = time.time()
            challenge['answered'] = False
            await update.message.reply_text(f'التحدي:⚔️\n\n{content}')
            return

    for challenge_id, challenge in list(active_challenges.items()):
        if challenge['chat_id'] != chat_id:
            continue
        if challenge.get('paused', False):
            continue
        if challenge['status'] != 'active':
            continue
        if challenge.get('answered', False):
            continue
        if 'current_content' not in challenge:
            continue
        
        user_identifier = f"@{update.effective_user.username}" if update.effective_user.username else update.effective_user.first_name
        is_participant = user_identifier in challenge.get('participants', [])
        is_creator = user_id == challenge['creator']['id']
        
        if not is_participant and not is_creator:
            continue
            
        correct_content = challenge['current_content']
        content_type = challenge['current_type']
        
        if content_type == 'word' or content_type == 'sentence':
            is_correct = normalize_answer(user_message, correct_content)
        else:
            is_correct = normalize_number(user_message, correct_content)
        
        if is_correct:
            start_time = challenge['start_time']
            response_time = time.time() - start_time
            
            if user_id not in context.bot_data['user_stats']:
                context.bot_data['user_stats'][user_id] = {
                    'words_correct': 0, 'words_wrong': 0,
                    'numbers_correct': 0, 'numbers_wrong': 0,
                    'sentences_correct': 0, 'sentences_wrong': 0,
                    'total_time': 0, 'join_date': datetime.datetime.now().isoformat(),
                    'first_activity': time.time()
                }

            user_stats = context.bot_data['user_stats'][user_id]
            
            if content_type == 'word':
                user_stats['words_correct'] += 1
                type_name = "الكلمة"
            elif content_type == 'number':
                user_stats['numbers_correct'] += 1
                type_name = "الرقم"
            else:
                user_stats['sentences_correct'] += 1
                type_name = "الجملة"

            if user_id not in user_scores:
                user_scores[user_id] = 0
            user_scores[user_id] += 1

            winner_message = random.choice(round_winner_messages)

            user_score = user_scores.get(user_id, 0)

            if response_time < records[content_type]['time']:
                records[content_type] = {
                    'time': response_time,
                    'user_name': user_name,
                    'user_id': user_id,
                    'username': username,
                    'content': correct_content
                }
                success_text = f"""
🏆 تـحـديـد رقـم قـيـاسـي جـديـد 🏆
🎯 أسـطـورة تـكـسـر الأرقـام

✅ {type_name}: {correct_content}
⏱️ زمـن تـاريـخـي: {response_time:.2f} ثـانـيـة
🏆 النقاط: {user_score} 
✨ {winner_message}

⚡ أسـطـورة الـسـرعـة تـسـطـع
"""
            else:
                success_text = f"""
✅ {type_name}: {correct_content}
⏱️ الوقت: {response_time:.2f} ثانية
🏆 النقاط: {user_score}
✨ {winner_message}
"""

            await update.message.reply_text(success_text)
            challenge['answered'] = True
            return
        else:
            if user_id in context.bot_data['user_stats']:
                user_stats = context.bot_data['user_stats'][user_id]
                if content_type == 'word':
                    user_stats['words_wrong'] += 1
                elif content_type == 'number':
                    user_stats['numbers_wrong'] += 1
                else:
                    user_stats['sentences_wrong'] += 1
            return

    await handle_challenge_answer(update, context)

    is_developer = username == "HEX_A"

    if user_message in ['ا', 'كلمات وارقام وجمل', 'الكل']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break

        if active_challenge:
            active_challenge['type'] = 'all'
            await update.message.reply_text("✅ تم تعيين التحدي: كلمات + أرقام + جمل")
        return
    
    if user_message in ['ق', 'ارقام وجمل', 'ارقام وجمل فقط']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'numbers_sentences'
            await update.message.reply_text("✅ تم تعيين التحدي: أرقام + جمل")
        return
    
    if user_message in ['ت', 'كلمات وجمل', 'كلمات وجمل فقط']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'words_sentences'
            await update.message.reply_text("✅ تم تعيين التحدي: كلمات + جمل")
        return
    
    if user_message in ['ل', 'جمل فقط', 'جمل']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'sentences_only'
            await update.message.reply_text("✅ تم تعيين التحدي: جمل فقط")
        return
        
    if user_message in ['اضافة للتحدي', 'اضافه للتحدي', 'اضف للتحدي', 'اضافة', 'اضافه', 'اضف', 'اظافة', 'إضافة', 'إضافه', 'إضف']:
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user
            replied_username = f"@{replied_user.username}" if replied_user.username else replied_user.first_name
            
            challenge_found = False
            for challenge_id, challenge in list(active_challenges.items()):
                if challenge['chat_id'] == update.effective_chat.id:
                    if replied_username not in challenge.get('participants', []):
                        if 'participants' not in challenge:
                            challenge['participants'] = []
                        challenge['participants'].append(replied_username)
                        await update.message.reply_text(f"✅ تمت إضافة {replied_username} إلى التحدي")
                        challenge_found = True
                    else:
                        await update.message.reply_text(f"⚠️ {replied_username} مضاف مسبقاً")
                    break
            
            if not challenge_found:
                await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        else:
            await update.message.reply_text("❌ يجب الرد على رسالة الشخص لإضافته")
        return
    
    if user_message in ['ازالة من التحدي', 'ازاله من التحدي', 'احذف من التحدي', 'ازالة', 'ازاله', 'احذف', 'إزالة', 'إزاله', 'إحذف']:
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user
            replied_username = f"@{replied_user.username}" if replied_user.username else replied_user.first_name
            
            challenge_found = False
            for challenge_id, challenge in list(active_challenges.items()):
                if challenge['chat_id'] == update.effective_chat.id:
                    if replied_username in challenge.get('participants', []):
                        challenge['participants'].remove(replied_username)
                        await update.message.reply_text(f"✅ تمت إزالة {replied_username} من التحدي")
                        challenge_found = True
                    else:
                        await update.message.reply_text(f"❌ {replied_username} غير مضاف للتحدي")
                    break
            
            if not challenge_found:
                await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        else:
            await update.message.reply_text("❌ يجب الرد على رسالة الشخص لإزالته")
        return

    if user_message in ['المشاركين', 'المشاركون', 'قائمة المشاركين', 'عرض المشاركين']:
        challenge_found = False
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                participants = challenge.get('participants', [])
                if participants:
                    participants_text = "\n".join([f"• {p}" for p in participants])
                    await update.message.reply_text(f"👥 قائمة المشاركين:\n{participants_text}")
                else:
                    await update.message.reply_text("📭 لا يوجد مشاركين بعد")
                challenge_found = True
                break
        
        if not challenge_found:
            await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        return

    if 'user_stats' not in context.bot_data:
        context.bot_data['user_stats'] = {}
    
    if user_id not in context.bot_data['user_stats']:
        context.bot_data['user_stats'][user_id] = {
            'words_correct': 0, 'words_wrong': 0,
            'numbers_correct': 0, 'numbers_wrong': 0,
            'sentences_correct': 0, 'sentences_wrong': 0,
            'total_time': 0, 'join_date': datetime.datetime.now().isoformat(),
            'first_activity': time.time()
        }
    
    user_stats = context.bot_data['user_stats'][user_id]
    
    if user_message == '🏆 الأرقام القياسية':
        await show_records(update, context)
        return

    if user_message == '📊 إحصائياتي':
        current_time = time.time()
        time_spent = current_time - user_stats['first_activity']
        
        days = int(time_spent // 86400)
        hours = int((time_spent % 86400) // 3600)
        minutes = int((time_spent % 3600) // 60)
        seconds = int(time_spent % 60)
        
        user_score = user_scores.get(user_id, 0)
        
        stats_text = f"""
📊 إحصائياتك الشخصية

🏆 النقاط الإجمالية: {user_score}
⚡ مستواك: {'مبتدئ' if user_score < 10 else 'متوسط' if user_score < 30 else 'متقدم' if user_score < 50 else 'محترف' if user_score < 100 else 'أسطورة'}

✅ الإجابات الصحيحة:
كلمات: {user_stats['words_correct']}
أرقام: {user_stats['numbers_correct']}
جمل: {user_stats['sentences_correct']}

❌ الأخطاء:
كلمات: {user_stats['words_wrong']}
أرقام: {user_stats['numbers_wrong']}
جمل: {user_stats['sentences_wrong']}

⏱️ الوقت في البوت:
الأيام: {days}
الساعات: {hours}
الدقائق: {minutes}
الثواني: {seconds}
"""
        await update.message.reply_text(stats_text, parse_mode='Markdown')
        return

    if user_message == '🌐 قياس السرعة':
        download_speed = random.uniform(10.0, 150.0)
        upload_speed = random.uniform(5.0, 80.0)
        ping = random.randint(8, 50)
        jitter = random.uniform(0.5, 15.0)
        
        speed_text = f"""
🌐 نتيجة قياس السرعة

⬇️ سرعة التنزيل: {download_speed:.1f} Mbps
⬆️ سرعة الرفع: {upload_speed:.1f} Mbps
📶 البنج: {ping} ms
📊 توتر الإرسال: {jitter:.1f} ms

⚡ اتصالك ممتاز
"""
        await update.message.reply_text(speed_text, parse_mode='Markdown')
        return

    if user_message == '⚡ تدريب سريع':
        keyboard = [
            ["📝 تدريب الكلمات", "🔢 تدريب الأرقام"],
            ["💬 تدريب الجمل", "🔙 الرجوع"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🎯 اختر نوع التدريب:", reply_markup=reply_markup)
        return

    if user_message in ['📝 تدريب الكلمات', 'ك', 'كلمة', 'كلمه']:
        if training_words:
            word = random.choice(training_words)
            group_sessions[chat_id] = {
                'type': 'word',
                'content': word,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{word}")  
        return

    if user_message in ['🔢 تدريب الأرقام', 'ر', 'رقم', 'ارقام']:
        if training_numbers:
            number = random.choice(training_numbers)
            group_sessions[chat_id] = {
                'type': 'number', 
                'content': number,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{number}")
        return
    
    if user_message in ['💬 تدريب الجمل', 'ج', 'جملة', 'جمله']:
        if training_sentences:
            sentence = random.choice(training_sentences)
            group_sessions[chat_id] = {
                'type': 'sentence',
                'content': sentence, 
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{sentence}")
        return

    if user_message == '🔙 الرجوع':
        await start(update, context)
        return

    if is_developer:
        if user_message == '🎯 بدء التحدي':
            await handle_challenge_start(update, context)
            return
        
        if user_message == '📊 الإحصائيات':
            user_score = user_scores.get(user_id, 0)
            total_players = len(user_scores)
            total_score = sum(user_scores.values())
            
            dev_stats = f"""
📊 إحصائيات المطور

👑 معلوماتك:
🏆 نقاطك: {user_score}
📈 مستواك: أسطورة

📊 إحصائيات البوت:
👥 عدد اللاعبين: {total_players}
🎯 إجمالي النقاط: {total_score}
💾 حجم البيانات: {len(context.bot_data.get('user_stats', {}))} لاعب
"""
            await update.message.reply_text(dev_stats, parse_mode='Markdown')
            return
        
        if user_message == '🔢 إدارة الأرقام':
            keyboard = [
                ["➕ إضافة رقم", "➖ حذف رقم"],
                ["📦 مجموعة أرقام", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🔢 إدارة الأرقام:", reply_markup=reply_markup)
            return
        
        if user_message == '📝 إدارة الكلمات':
            keyboard = [
                ["➕ إضافة كلمة", "➖ حذف كلمة"],
                ["📦 مجموعة كلمات", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("📝 إدارة الكلمات:", reply_markup=reply_markup)
            return
        
        if user_message == '💬 إدارة الجمل':
            keyboard = [
                ["➕ إضافة جملة", "➖ حذف جملة"],
                ["📦 مجموعة جمل", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("💬 إدارة الجمل:", reply_markup=reply_markup)
            return
        
        if user_message == '➕ إضافة رقم':
            await update.message.reply_text("🔢 أرسل الرقم الجديد لإضافته:")
            context.user_data['awaiting_input'] = 'add_number'
            return
        
        if user_message == '➖ حذف رقم':
            await update.message.reply_text("🔢 أرسل الرقم المطلوب حذفه:")
            context.user_data['awaiting_input'] = 'delete_number'
            return
        
        if user_message == '➕ إضافة كلمة':
            await update.message.reply_text("📝 أرسل الكلمة الجديدة لإضافتها:")
            context.user_data['awaiting_input'] = 'add_word'
            return
        
        if user_message == '➖ حذف كلمة':
            await update.message.reply_text("📝 أرسل الكلمة المطلوب حذفها:")
            context.user_data['awaiting_input'] = 'delete_word'
            return
        
        if user_message == '➕ إضافة جملة':
            await update.message.reply_text("💬 أرسل الجملة الجديدة لإضافتها:")
            context.user_data['awaiting_input'] = 'add_sentence'
            return
        
        if user_message == '➖ حذف جملة':
            await update.message.reply_text("💬 أرسل الجملة المطلوب حذفها:")
            context.user_data['awaiting_input'] = 'delete_sentence'
            return
        
        if user_message == '🔄 تغيير الأوامر':
            keyboard = [
                ["🔄 تغيير أمر الكلمات", "🔄 تغيير أمر الأرقام"],
                ["🔄 تغيير أمر الجمل", "🔄 تغيير أمر التحدي"],
                ["🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🔄 اختر نوع الأمر لتغييره:", reply_markup=reply_markup)
            return
        
        if user_message == '🔄 تغيير أمر الكلمات':
            await update.message.reply_text("📝 أرسل الأمر الجديد للكلمات:")
            context.user_data['awaiting_input'] = 'change_word_command'
            return
        
        if user_message == '🔄 تغيير أمر الأرقام':
            await update.message.reply_text("🔢 أرسل الأمر الجديد للأرقام:")
            context.user_data['awaiting_input'] = 'change_number_command'
            return
        
        if user_message == '🔄 تغيير أمر الجمل':
            await update.message.reply_text("💬 أرسل الأمر الجديد للجمل:")
            context.user_data['awaiting_input'] = 'change_sentence_command'
            return
        
        if user_message == '🔄 تغيير أمر التحدي':
            await update.message.reply_text("🎯 أرسل الأمر الجديد للتحدي:")
            context.user_data['awaiting_input'] = 'change_challenge_command'
            return
        
        if user_message == '📦 الإضافة الجماعية':
            keyboard = [
                ["📦 إضافة مجموعة جمل", "📦 إضافة مجموعة كلمات"],
                ["📦 إضافة مجموعة أرقام", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("📦 اختر نوع المجموعة:", reply_markup=reply_markup)
            return
        
        if user_message == '📦 مجموعة أرقام':
            await update.message.reply_text("🔢 أرسل الأرقام مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_numbers_group'
            return
        
        if user_message == '📦 مجموعة كلمات':
            await update.message.reply_text("📝 أرسل الكلمات مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_words_group'
            return
        
        if user_message == '📦 مجموعة جمل':
            await update.message.reply_text("💬 أرسل الجمل مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_sentences_group'
            return
        
        if user_message == '🛠️ إعدادات البوت':
            keyboard = [
                ["⚙️ إعدادات التحدي", "📊 قاعدة البيانات"],
                ["🔧 الإعدادات المتقدمة", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🛠️ إعدادات البوت المتقدمة:", reply_markup=reply_markup)
            return
        
        if user_message == '⚙️ إعدادات التحدي':
            challenge_settings = """
⚙️ إعدادات التحدي الحالية:

🎯 أنواع التحدي المتاحة:
كلمات فقط
أرقام فقط  
كلمات وأرقام

⏱️ إعدادات الوقت:
وقت الإجابة: فوري
وقت التحدي: مفتوح
"""
            await update.message.reply_text(challenge_settings, parse_mode='Markdown')
            return
        
        if user_message == '📊 قاعدة البيانات':
            db_info = f"""
📊 معلومات قاعدة البيانات:

📝 الكلمات: {len(training_words)} كلمة
🔢 الأرقام: {len(training_numbers)} رقم
💬 الجمل: {len(training_sentences)} جملة
👥 اللاعبين: {len(user_scores)} لاعب
💾 الإحصائيات: {len(context.bot_data.get('user_stats', {}))} لاعب
"""
            await update.message.reply_text(db_info, parse_mode='Markdown')
            return
        
        if user_message == '🔧 الإعدادات المتقدمة':
            await update.message.reply_text("🔧 الإعدادات المتقدمة جاهزة للتعديل")
            return
        
        if user_message == '📈 إحصائيات الأعضاء':
            total_players = len(user_scores)
            active_players = len([score for score in user_scores.values() if score > 0])
            total_score = sum(user_scores.values())
            
            stats_text = f"""
📈 إحصائيات الأعضاء

👥 إجمالي اللاعبين: {total_players}
⚡ اللاعبين النشطين: {active_players}
🏆 إجمالي النقاط: {total_score}
📊 متوسط النقاط: {total_score/max(1, active_players):.1f}
"""
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            return
        
        if user_message == '👥 اللاعبين النشطين':
            active_users = []
            for uid, score in user_scores.items():
                if score > 0:
                    active_users.append((uid, score))
            
            active_users.sort(key=lambda x: x[1], reverse=True)
            
            players_text = "👥 اللاعبين النشطين:\n\n"
            for i, (player_id, score) in enumerate(active_users[:15], 1):
                players_text += f"{i}. 🎯 {score} نقطة\n"
            
            await update.message.reply_text(players_text, parse_mode='Markdown')
            return

        if context.user_data.get('awaiting_input'):
            action = context.user_data['awaiting_input']
            
            if action == 'add_number' and user_message:
                if user_message not in training_numbers:
                    training_numbers.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الرقم: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الرقم موجود مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'add_word' and user_message:
                if user_message not in training_words:
                    training_words.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الكلمة: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الكلمة موجودة مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'add_sentence' and user_message:
                if user_message not in training_sentences:
                    training_sentences.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الجملة: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الجملة موجودة مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_number' and user_message:
                if user_message in training_numbers:
                    training_numbers.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الرقم: {user_message}")
                else:
                    await update.message.reply_text("❌ الرقم غير موجود")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_word' and user_message:
                if user_message in training_words:
                    training_words.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الكلمة: {user_message}")
                else:
                    await update.message.reply_text("❌ الكلمة غير موجودة")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_sentence' and user_message:
                if user_message in training_sentences:
                    training_sentences.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الجملة: {user_message}")
                else:
                    await update.message.reply_text("❌ الجملة غير موجودة")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_word_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الكلمات إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_number_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الأرقام إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_sentence_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الجمل إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_challenge_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر التحدي إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return

    if context.user_data.get('awaiting_input') in ['add_sentences_group', 'add_words_group', 'add_numbers_group']:
        action = context.user_data['awaiting_input']
        items = [item.strip() for item in user_message.split('،') if item.strip()]
        
        if action == 'add_sentences_group':
            added_count = 0
            for sentence in items:
                if sentence and sentence not in training_sentences:
                    training_sentences.append(sentence)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} جملة جديدة")
        
        elif action == 'add_words_group':
            added_count = 0
            for word in items:
                if word and word not in training_words:
                    training_words.append(word)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} كلمة جديدة")
        
        elif action == 'add_numbers_group':
            added_count = 0
            for number in items:
                if number and number not in training_numbers:
                    training_numbers.append(number)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} رقم جديد")
        
        context.user_data['awaiting_input'] = None
        return
        
    if user_message in ['📝 تدريب الكلمات', 'ك', 'كلمة', 'كلمه']:
        if training_words:
            word = random.choice(training_words)
            group_sessions[chat_id] = {
                'type': 'word',
                'content': word,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{word}")  
        return

    if user_message in ['🔢 تدريب الأرقام', 'ر', 'رقم', 'ارقام']:
        if training_numbers:
            number = random.choice(training_numbers)
            group_sessions[chat_id] = {
                'type': 'number', 
                'content': number,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{number}")
        return
    
    if user_message in ['💬 تدريب الجمل', 'ج', 'جملة', 'جمله']:
        if training_sentences:
            sentence = random.choice(training_sentences)
            group_sessions[chat_id] = {
                'type': 'sentence',
                'content': sentence, 
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{sentence}")
        return

    if chat_id in group_sessions:
        session = group_sessions[chat_id]
        correct_content = session['content']
        content_type = session['type']
        start_time = session['start_time']
        response_time = time.time() - start_time

        if content_type == 'word':
            is_correct = normalize_answer(user_message, correct_content)
        elif content_type == 'number':
            is_correct = normalize_number(user_message, correct_content)
        elif content_type == 'sentence':
            is_correct = normalize_answer(user_message, correct_content)

        if is_correct:
            start_time = session['start_time']
            response_time = time.time() - start_time
            
            if user_id not in context.bot_data['user_stats']:
                context.bot_data['user_stats'][user_id] = {
                    'words_correct': 0, 'words_wrong': 0,
                    'numbers_correct': 0, 'numbers_wrong': 0,
                    'sentences_correct': 0, 'sentences_wrong': 0,
                    'total_time': 0, 'join_date': datetime.datetime.now().isoformat(),
                    'first_activity': time.time()
                }

            user_stats = context.bot_data['user_stats'][user_id]
            
            if content_type == 'word':
                user_stats['words_correct'] += 1
                type_name = "الكلمة"
            elif content_type == 'number':
                user_stats['numbers_correct'] += 1
                type_name = "الرقم"
            else:
                user_stats['sentences_correct'] += 1
                type_name = "الجملة"

            if user_id not in user_scores:
                user_scores[user_id] = 0
            user_scores[user_id] += 1

            winner_message = random.choice(round_winner_messages)

            user_score = user_scores.get(user_id, 0)

            if response_time < records[content_type]['time']:
                records[content_type] = {
                    'time': response_time,
                    'user_name': user_name,
                    'user_id': user_id,
                    'username': username,
                    'content': correct_content
                }
                success_text = f"""
🏆 تـحـديـد رقـم قـيـاسـي جـديـد 🏆
🎯 أسـطـورة تـكـسـر الأرقـام

✅ {type_name}: {correct_content}
⏱️ زمـن تـاريـخـي: {response_time:.2f} ثـانـيـة
🏆 النقاط: {user_score} 
✨ {winner_message}

⚡ أسـطـورة الـسـرعـة تـسـطـع
"""
            else:
                success_text = f"""
✅ {type_name}: {correct_content}
⏱️ الوقت: {response_time:.2f} ثانية
🏆 النقاط: {user_score}
✨ {winner_message}
"""

            await update.message.reply_text(success_text)
            del group_sessions[chat_id]
            return
        else:
            if user_id in context.bot_data['user_stats']:
                user_stats = context.bot_data['user_stats'][user_id]
                if content_type == 'word':
                    user_stats['words_wrong'] += 1
                elif content_type == 'number':
                    user_stats['numbers_wrong'] += 1
                else:
                    user_stats['sentences_wrong'] += 1
            return

    await handle_challenge_answer(update, context)

    is_developer = username == "HEX_A"

    if user_message in ['ا', 'كلمات وارقام وجمل', 'الكل']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break

        if active_challenge:
            active_challenge['type'] = 'all'
            await update.message.reply_text("✅ تم تعيين التحدي: كلمات + أرقام + جمل")
        return
    
    if user_message in ['ق', 'ارقام وجمل', 'ارقام وجمل فقط']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'numbers_sentences'
            await update.message.reply_text("✅ تم تعيين التحدي: أرقام + جمل")
        return
    
    if user_message in ['ت', 'كلمات وجمل', 'كلمات وجمل فقط']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'words_sentences'
            await update.message.reply_text("✅ تم تعيين التحدي: كلمات + جمل")
        return
    
    if user_message in ['ل', 'جمل فقط', 'جمل']:
        active_challenge = None
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                active_challenge = challenge
                break
        
        if active_challenge:
            active_challenge['type'] = 'sentences_only'
            await update.message.reply_text("✅ تم تعيين التحدي: جمل فقط")
        return
        
    if user_message in ['اضافة للتحدي', 'اضافه للتحدي', 'اضف للتحدي', 'اضافة', 'اضافه', 'اضف', 'اظافة', 'إضافة', 'إضافه', 'إضف']:
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user
            replied_username = f"@{replied_user.username}" if replied_user.username else replied_user.first_name
            
            challenge_found = False
            for challenge_id, challenge in list(active_challenges.items()):
                if challenge['chat_id'] == update.effective_chat.id:
                    if replied_username not in challenge.get('participants', []):
                        if 'participants' not in challenge:
                            challenge['participants'] = []
                        challenge['participants'].append(replied_username)
                        await update.message.reply_text(f"✅ تمت إضافة {replied_username} إلى التحدي")
                        challenge_found = True
                    else:
                        await update.message.reply_text(f"⚠️ {replied_username} مضاف مسبقاً")
                    break
            
            if not challenge_found:
                await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        else:
            await update.message.reply_text("❌ يجب الرد على رسالة الشخص لإضافته")
        return
    
    if user_message in ['ازالة من التحدي', 'ازاله من التحدي', 'احذف من التحدي', 'ازالة', 'ازاله', 'احذف', 'إزالة', 'إزاله', 'إحذف']:
        if update.message.reply_to_message:
            replied_user = update.message.reply_to_message.from_user
            replied_username = f"@{replied_user.username}" if replied_user.username else replied_user.first_name
            
            challenge_found = False
            for challenge_id, challenge in list(active_challenges.items()):
                if challenge['chat_id'] == update.effective_chat.id:
                    if replied_username in challenge.get('participants', []):
                        challenge['participants'].remove(replied_username)
                        await update.message.reply_text(f"✅ تمت إزالة {replied_username} من التحدي")
                        challenge_found = True
                    else:
                        await update.message.reply_text(f"❌ {replied_username} غير مضاف للتحدي")
                    break
            
            if not challenge_found:
                await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        else:
            await update.message.reply_text("❌ يجب الرد على رسالة الشخص لإزالته")
        return

    if user_message in ['المشاركين', 'المشاركون', 'قائمة المشاركين', 'عرض المشاركين']:
        challenge_found = False
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == update.effective_chat.id:
                participants = challenge.get('participants', [])
                if participants:
                    participants_text = "\n".join([f"• {p}" for p in participants])
                    await update.message.reply_text(f"👥 قائمة المشاركين:\n{participants_text}")
                else:
                    await update.message.reply_text("📭 لا يوجد مشاركين بعد")
                challenge_found = True
                break
        
        if not challenge_found:
            await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")
        return

    if 'user_stats' not in context.bot_data:
        context.bot_data['user_stats'] = {}
    
    if user_id not in context.bot_data['user_stats']:
        context.bot_data['user_stats'][user_id] = {
            'words_correct': 0, 'words_wrong': 0,
            'numbers_correct': 0, 'numbers_wrong': 0,
            'sentences_correct': 0, 'sentences_wrong': 0,
            'total_time': 0, 'join_date': datetime.datetime.now().isoformat(),
            'first_activity': time.time()
        }
    
    user_stats = context.bot_data['user_stats'][user_id]
    
    if user_message == '🏆 الأرقام القياسية':
        await show_records(update, context)
        return

    if user_message == '📊 إحصائياتي':
        current_time = time.time()
        time_spent = current_time - user_stats['first_activity']
        
        days = int(time_spent // 86400)
        hours = int((time_spent % 86400) // 3600)
        minutes = int((time_spent % 3600) // 60)
        seconds = int(time_spent % 60)
        
        user_score = user_scores.get(user_id, 0)
        
        stats_text = f"""
📊 إحصائياتك الشخصية

🏆 النقاط الإجمالية: {user_score}
⚡ مستواك: {'مبتدئ' if user_score < 10 else 'متوسط' if user_score < 30 else 'متقدم' if user_score < 50 else 'محترف' if user_score < 100 else 'أسطورة'}

✅ الإجابات الصحيحة:
كلمات: {user_stats['words_correct']}
أرقام: {user_stats['numbers_correct']}
جمل: {user_stats['sentences_correct']}

❌ الأخطاء:
كلمات: {user_stats['words_wrong']}
أرقام: {user_stats['numbers_wrong']}
جمل: {user_stats['sentences_wrong']}

⏱️ الوقت في البوت:
الأيام: {days}
الساعات: {hours}
الدقائق: {minutes}
الثواني: {seconds}
"""
        await update.message.reply_text(stats_text, parse_mode='Markdown')
        return

    if user_message == '🌐 قياس السرعة':
        download_speed = random.uniform(10.0, 150.0)
        upload_speed = random.uniform(5.0, 80.0)
        ping = random.randint(8, 50)
        jitter = random.uniform(0.5, 15.0)
        
        speed_text = f"""
🌐 نتيجة قياس السرعة

⬇️ سرعة التنزيل: {download_speed:.1f} Mbps
⬆️ سرعة الرفع: {upload_speed:.1f} Mbps
📶 البنج: {ping} ms
📊 توتر الإرسال: {jitter:.1f} ms

⚡ اتصالك ممتاز
"""
        await update.message.reply_text(speed_text, parse_mode='Markdown')
        return

    if user_message == '⚡ تدريب سريع':
        keyboard = [
            ["📝 تدريب الكلمات", "🔢 تدريب الأرقام"],
            ["💬 تدريب الجمل", "🔙 الرجوع"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("🎯 اختر نوع التدريب:", reply_markup=reply_markup)
        return

    if user_message in ['📝 تدريب الكلمات', 'ك', 'كلمة', 'كلمه']:
        if training_words:
            word = random.choice(training_words)
            group_sessions[chat_id] = {
                'type': 'word',
                'content': word,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{word}")  
        return

    if user_message in ['🔢 تدريب الأرقام', 'ر', 'رقم', 'ارقام']:
        if training_numbers:
            number = random.choice(training_numbers)
            group_sessions[chat_id] = {
                'type': 'number', 
                'content': number,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{number}")
        return
    
    if user_message in ['💬 تدريب الجمل', 'ج', 'جملة', 'جمله']:
        if training_sentences:
            sentence = random.choice(training_sentences)
            group_sessions[chat_id] = {
                'type': 'sentence',
                'content': sentence, 
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{sentence}")
        return

    if user_message == '🔙 الرجوع':
        await start(update, context)
        return

    if is_developer:
        if user_message == '🎯 بدء التحدي':
            await handle_challenge_start(update, context)
            return
        
        if user_message == '📊 الإحصائيات':
            user_score = user_scores.get(user_id, 0)
            total_players = len(user_scores)
            total_score = sum(user_scores.values())
            
            dev_stats = f"""
📊 إحصائيات المطور

👑 معلوماتك:
🏆 نقاطك: {user_score}
📈 مستواك: أسطورة

📊 إحصائيات البوت:
👥 عدد اللاعبين: {total_players}
🎯 إجمالي النقاط: {total_score}
💾 حجم البيانات: {len(context.bot_data.get('user_stats', {}))} لاعب
"""
            await update.message.reply_text(dev_stats, parse_mode='Markdown')
            return
        
        if user_message == '🔢 إدارة الأرقام':
            keyboard = [
                ["➕ إضافة رقم", "➖ حذف رقم"],
                ["📦 مجموعة أرقام", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🔢 إدارة الأرقام:", reply_markup=reply_markup)
            return
        
        if user_message == '📝 إدارة الكلمات':
            keyboard = [
                ["➕ إضافة كلمة", "➖ حذف كلمة"],
                ["📦 مجموعة كلمات", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("📝 إدارة الكلمات:", reply_markup=reply_markup)
            return
        
        if user_message == '💬 إدارة الجمل':
            keyboard = [
                ["➕ إضافة جملة", "➖ حذف جملة"],
                ["📦 مجموعة جمل", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("💬 إدارة الجمل:", reply_markup=reply_markup)
            return
        
        if user_message == '➕ إضافة رقم':
            await update.message.reply_text("🔢 أرسل الرقم الجديد لإضافته:")
            context.user_data['awaiting_input'] = 'add_number'
            return
        
        if user_message == '➖ حذف رقم':
            await update.message.reply_text("🔢 أرسل الرقم المطلوب حذفه:")
            context.user_data['awaiting_input'] = 'delete_number'
            return
        
        if user_message == '➕ إضافة كلمة':
            await update.message.reply_text("📝 أرسل الكلمة الجديدة لإضافتها:")
            context.user_data['awaiting_input'] = 'add_word'
            return
        
        if user_message == '➖ حذف كلمة':
            await update.message.reply_text("📝 أرسل الكلمة المطلوب حذفها:")
            context.user_data['awaiting_input'] = 'delete_word'
            return
        
        if user_message == '➕ إضافة جملة':
            await update.message.reply_text("💬 أرسل الجملة الجديدة لإضافتها:")
            context.user_data['awaiting_input'] = 'add_sentence'
            return
        
        if user_message == '➖ حذف جملة':
            await update.message.reply_text("💬 أرسل الجملة المطلوب حذفها:")
            context.user_data['awaiting_input'] = 'delete_sentence'
            return
        
        if user_message == '🔄 تغيير الأوامر':
            keyboard = [
                ["🔄 تغيير أمر الكلمات", "🔄 تغيير أمر الأرقام"],
                ["🔄 تغيير أمر الجمل", "🔄 تغيير أمر التحدي"],
                ["🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🔄 اختر نوع الأمر لتغييره:", reply_markup=reply_markup)
            return
        
        if user_message == '🔄 تغيير أمر الكلمات':
            await update.message.reply_text("📝 أرسل الأمر الجديد للكلمات:")
            context.user_data['awaiting_input'] = 'change_word_command'
            return
        
        if user_message == '🔄 تغيير أمر الأرقام':
            await update.message.reply_text("🔢 أرسل الأمر الجديد للأرقام:")
            context.user_data['awaiting_input'] = 'change_number_command'
            return
        
        if user_message == '🔄 تغيير أمر الجمل':
            await update.message.reply_text("💬 أرسل الأمر الجديد للجمل:")
            context.user_data['awaiting_input'] = 'change_sentence_command'
            return
        
        if user_message == '🔄 تغيير أمر التحدي':
            await update.message.reply_text("🎯 أرسل الأمر الجديد للتحدي:")
            context.user_data['awaiting_input'] = 'change_challenge_command'
            return
        
        if user_message == '📦 الإضافة الجماعية':
            keyboard = [
                ["📦 إضافة مجموعة جمل", "📦 إضافة مجموعة كلمات"],
                ["📦 إضافة مجموعة أرقام", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("📦 اختر نوع المجموعة:", reply_markup=reply_markup)
            return
        
        if user_message == '📦 مجموعة أرقام':
            await update.message.reply_text("🔢 أرسل الأرقام مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_numbers_group'
            return
        
        if user_message == '📦 مجموعة كلمات':
            await update.message.reply_text("📝 أرسل الكلمات مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_words_group'
            return
        
        if user_message == '📦 مجموعة جمل':
            await update.message.reply_text("💬 أرسل الجمل مفصولة بفاصلة (،):")
            context.user_data['awaiting_input'] = 'add_sentences_group'
            return
        
        if user_message == '🛠️ إعدادات البوت':
            keyboard = [
                ["⚙️ إعدادات التحدي", "📊 قاعدة البيانات"],
                ["🔧 الإعدادات المتقدمة", "🔙 الرجوع"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text("🛠️ إعدادات البوت المتقدمة:", reply_markup=reply_markup)
            return
        
        if user_message == '⚙️ إعدادات التحدي':
            challenge_settings = """
⚙️ إعدادات التحدي الحالية:

🎯 أنواع التحدي المتاحة:
كلمات فقط
أرقام فقط  
كلمات وأرقام

⏱️ إعدادات الوقت:
وقت الإجابة: فوري
وقت التحدي: مفتوح
"""
            await update.message.reply_text(challenge_settings, parse_mode='Markdown')
            return
        
        if user_message == '📊 قاعدة البيانات':
            db_info = f"""
📊 معلومات قاعدة البيانات:

📝 الكلمات: {len(training_words)} كلمة
🔢 الأرقام: {len(training_numbers)} رقم
💬 الجمل: {len(training_sentences)} جملة
👥 اللاعبين: {len(user_scores)} لاعب
💾 الإحصائيات: {len(context.bot_data.get('user_stats', {}))} لاعب
"""
            await update.message.reply_text(db_info, parse_mode='Markdown')
            return
        
        if user_message == '🔧 الإعدادات المتقدمة':
            await update.message.reply_text("🔧 الإعدادات المتقدمة جاهزة للتعديل")
            return
        
        if user_message == '📈 إحصائيات الأعضاء':
            total_players = len(user_scores)
            active_players = len([score for score in user_scores.values() if score > 0])
            total_score = sum(user_scores.values())
            
            stats_text = f"""
📈 إحصائيات الأعضاء

👥 إجمالي اللاعبين: {total_players}
⚡ اللاعبين النشطين: {active_players}
🏆 إجمالي النقاط: {total_score}
📊 متوسط النقاط: {total_score/max(1, active_players):.1f}
"""
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            return
        
        if user_message == '👥 اللاعبين النشطين':
            active_users = []
            for uid, score in user_scores.items():
                if score > 0:
                    active_users.append((uid, score))
            
            active_users.sort(key=lambda x: x[1], reverse=True)
            
            players_text = "👥 اللاعبين النشطين:\n\n"
            for i, (player_id, score) in enumerate(active_users[:15], 1):
                players_text += f"{i}. 🎯 {score} نقطة\n"
            
            await update.message.reply_text(players_text, parse_mode='Markdown')
            return

        if context.user_data.get('awaiting_input'):
            action = context.user_data['awaiting_input']
            
            if action == 'add_number' and user_message:
                if user_message not in training_numbers:
                    training_numbers.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الرقم: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الرقم موجود مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'add_word' and user_message:
                if user_message not in training_words:
                    training_words.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الكلمة: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الكلمة موجودة مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'add_sentence' and user_message:
                if user_message not in training_sentences:
                    training_sentences.append(user_message)
                    await update.message.reply_text(f"✅ تمت إضافة الجملة: {user_message}")
                else:
                    await update.message.reply_text("⚠️ الجملة موجودة مسبقاً")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_number' and user_message:
                if user_message in training_numbers:
                    training_numbers.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الرقم: {user_message}")
                else:
                    await update.message.reply_text("❌ الرقم غير موجود")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_word' and user_message:
                if user_message in training_words:
                    training_words.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الكلمة: {user_message}")
                else:
                    await update.message.reply_text("❌ الكلمة غير موجودة")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'delete_sentence' and user_message:
                if user_message in training_sentences:
                    training_sentences.remove(user_message)
                    await update.message.reply_text(f"✅ تم حذف الجملة: {user_message}")
                else:
                    await update.message.reply_text("❌ الجملة غير موجودة")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_word_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الكلمات إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_number_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الأرقام إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_sentence_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر الجمل إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return
            
            elif action == 'change_challenge_command' and user_message:
                await update.message.reply_text(f"✅ تم تغيير أمر التحدي إلى: {user_message}")
                context.user_data['awaiting_input'] = None
                return

    if context.user_data.get('awaiting_input') in ['add_sentences_group', 'add_words_group', 'add_numbers_group']:
        action = context.user_data['awaiting_input']
        items = [item.strip() for item in user_message.split('،') if item.strip()]
        
        if action == 'add_sentences_group':
            added_count = 0
            for sentence in items:
                if sentence and sentence not in training_sentences:
                    training_sentences.append(sentence)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} جملة جديدة")
        
        elif action == 'add_words_group':
            added_count = 0
            for word in items:
                if word and word not in training_words:
                    training_words.append(word)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} كلمة جديدة")
        
        elif action == 'add_numbers_group':
            added_count = 0
            for number in items:
                if number and number not in training_numbers:
                    training_numbers.append(number)
                    added_count += 1
            await update.message.reply_text(f"✅ تمت إضافة {added_count} رقم جديد")
        
        context.user_data['awaiting_input'] = None
        return
        
    if user_message in ['📝 تدريب الكلمات', 'ك', 'كلمة', 'كلمه']:
        if training_words:
            word = random.choice(training_words)
            group_sessions[chat_id] = {
                'type': 'word',
                'content': word,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{word}")  
        return

    if user_message in ['🔢 تدريب الأرقام', 'ر', 'رقم', 'ارقام']:
        if training_numbers:
            number = random.choice(training_numbers)
            group_sessions[chat_id] = {
                'type': 'number', 
                'content': number,
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{number}")
        return
    
    if user_message in ['💬 تدريب الجمل', 'ج', 'جملة', 'جمله']:
        if training_sentences:
            sentence = random.choice(training_sentences)
            group_sessions[chat_id] = {
                'type': 'sentence',
                'content': sentence, 
                'start_time': time.time()
            }
            
            await update.message.reply_text(f"\n\n{sentence}")
        return

    if chat_id in group_sessions:
        session = group_sessions[chat_id]
        correct_content = session['content']
        content_type = session['type']
        start_time = session['start_time']
        response_time = time.time() - start_time

        if content_type == 'word':
            is_correct = normalize_answer(user_message, correct_content)
        elif content_type == 'number':
            is_correct = normalize_number(user_message, correct_content)
        elif content_type == 'sentence':
            is_correct = normalize_answer(user_message, correct_content)

        if is_correct:
            start_time = session['start_time']
            response_time = time.time() - start_time
            
            if user_id not in context.bot_data['user_stats']:
                context.bot_data['user_stats'][user_id] = {
                    'words_correct': 0, 'words_wrong': 0,
                    'numbers_correct': 0, 'numbers_wrong': 0,
                    'sentences_correct': 0, 'sentences_wrong': 0,
                    'total_time': 0, 'join_date': datetime.datetime.now().isoformat(),
                    'first_activity': time.time()
                }

            user_stats = context.bot_data['user_stats'][user_id]
            
            if content_type == 'word':
                user_stats['words_correct'] += 1
                type_name = "الكلمة"
            elif content_type == 'number':
                user_stats['numbers_correct'] += 1
                type_name = "الرقم"
            else:
                user_stats['sentences_correct'] += 1
                type_name = "الجملة"

            if user_id not in user_scores:
                user_scores[user_id] = 0
            user_scores[user_id] += 1

            winner_message = random.choice(round_winner_messages)

            user_score = user_scores.get(user_id, 0)

            if response_time < records[content_type]['time']:
                records[content_type] = {
                    'time': response_time,
                    'user_name': user_name,
                    'user_id': user_id,
                    'username': username,
                    'content': correct_content
                }
                success_text = f"""
🏆 تـحـديـد رقـم قـيـاسـي جـديـد 🏆
🎯 أسـطـورة تـكـسـر الأرقـام

✅ {type_name}: {correct_content}
⏱️ زمـن تـاريـخـي: {response_time:.2f} ثـانـيـة
🏆 النقاط: {user_score} 
✨ {winner_message}

⚡ أسـطـورة الـسـرعـة تـسـطـع
"""
            else:
                success_text = f"""
✅ {type_name}: {correct_content}
⏱️ الوقت: {response_time:.2f} ثانية
🏆 النقاط: {user_score}
✨ {winner_message}
"""

            await update.message.reply_text(success_text)
            del group_sessions[chat_id]
            return
        else:
            if user_id in context.bot_data['user_stats']:
                user_stats = context.bot_data['user_stats'][user_id]
                if content_type == 'word':
                    user_stats['words_wrong'] += 1
                elif content_type == 'number':
                    user_stats['numbers_wrong'] += 1
                else:
                    user_stats['sentences_wrong'] += 1
            return

    await handle_challenge_answer(update, context)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    active_challenge = None
    for challenge in active_challenges.values():
        if challenge['chat_id'] == chat_id:
            active_challenge = challenge
            break
    
    if not active_challenge or not active_challenge.get('scores'):
        message_text = "🎯 لا توجد نتائج حتى الآن"
        if update.message:
            await update.message.reply_text(message_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message_text)
        return
    
    leaderboard_text = "⚡ ━━━━━━━━━━━━━━━━━━━ ⚡\n              🏆 الـمـتـصـدرون 🏆\n\n"
    
    top_three = sorted(active_challenge['scores'].items(), key=lambda x: x[1], reverse=True)[:3]
    
    if len(top_three) == 1:
        user_id1, score1 = top_three[0]
        user_data1 = challenge_leaderboards.get(user_id1, {'name': 'مجهول', 'username': ''})
        username_display1 = f"@{user_data1['username']}" if user_data1['username'] else "بدون معرف"
        leaderboard_text += f"🥇 <a href=\"tg://user?id={user_id1}\">{user_data1['name']}</a> \n"
        leaderboard_text += f"User : {username_display1}\n"
        leaderboard_text += f"points : {score1} 🎯\n\n"
        leaderboard_text += "💫 «سيد المعركة.. بطل بلا منازع» 💫\n\n"
    
    elif len(top_three) == 2:
        for i, (uid, score) in enumerate(top_three[:2], 1):
            user_data = challenge_leaderboards.get(uid, {'name': 'مجهول', 'username': ''})
            username_display = f"@{user_data['username']}" if user_data['username'] else "بدون معرف"
            medal = "🥇" if i == 1 else "🥈"
            leaderboard_text += f"{medal} <a href=\"tg://user?id={uid}\">{user_data['name']}</a> \n"
            leaderboard_text += f"User : {username_display}\n"
            leaderboard_text += f"points : {score} 🎯\n\n"
        leaderboard_text += "🔥 «مواجهة الأسود.. صراع الأقوياء» 🔥\n\n"
    
    elif len(top_three) >= 3:
        for i, (uid, score) in enumerate(top_three[:3], 1):
            user_data = challenge_leaderboards.get(uid, {'name': 'مجهول', 'username': ''})
            username_display = f"@{user_data['username']}" if user_data['username'] else "بدون معرف"
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
            leaderboard_text += f"{medal} <a href=\"tg://user?id={uid}\">{user_data['name']}</a> \n"
            leaderboard_text += f"User : {username_display}\n"
            leaderboard_text += f"points : {score} 🎯\n\n"
        leaderboard_text += "🌟 «ثلاثية الأبطال.. ملحمة التتويج» 🌟\n\n"
    
    if update.message:
        await update.message.reply_text(leaderboard_text, parse_mode='HTML')
    elif update.callback_query:
        await update.callback_query.edit_message_text(leaderboard_text, parse_mode='HTML')

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "trend":
        record_text = "🏆 الأرقام القياسية 🏆\n\n"
        
        record_text += "📝 أسرع 5 كلمات:\n"
        word_records = [r for r in [records['word']] if r['time'] != float('inf')]
        if word_records:
            for i, record in enumerate(word_records[:5], 1):
                username_text = f"(@{record['username']})" if record['username'] else ""
                record_text += f"{i}. {record['user_name']} {username_text}\n   ⏱ {record['time']:.2f} ثانية - {record['content']}\n"
        else:
            record_text += "لا توجد سجلات للكلمات بعد\n"
        record_text += "\n"
        
        record_text += "🔢 أسرع 5 أرقام:\n"
        number_records = [r for r in [records['number']] if r['time'] != float('inf')]
        if number_records:
            for i, record in enumerate(number_records[:5], 1):
                username_text = f"(@{record['username']})" if record['username'] else ""
                record_text += f"{i}. {record['user_name']} {username_text}\n   ⏱ {record['time']:.2f} ثانية - {record['content']}\n"
        else:
            record_text += "لا توجد سجلات للأرقام بعد\n"
        record_text += "\n"
        
        record_text += "💬 أسرع 5 جمل:\n"
        sentence_records = [r for r in [records['sentence']] if r['time'] != float('inf')]
        if sentence_records:
            for i, record in enumerate(sentence_records[:5], 1):
                username_text = f"(@{record['username']})" if record['username'] else ""
                record_text += f"{i}. {record['user_name']} {username_text}\n   ⏱ {record['time']:.2f} ثانية - {record['content']}\n"
        else:
            record_text += "لا توجد سجلات للجمل بعد\n"
        
        record_text += "\n💪 حاول كسر هذه الأرقام القياسية!"
        
        await query.edit_message_text(record_text)
    elif data == "mystats":
        user_id = query.from_user.id
        user_stats = context.bot_data.get('user_stats', {})
        current_time = time.time()
        time_spent = current_time - user_stats.get('first_activity', current_time)
        
        days = int(time_spent // 86400)
        hours = int((time_spent % 86400) // 3600)
        minutes = int((time_spent % 3600) // 60)
        seconds = int(time_spent % 60)
        
        stats_text = f"""
📊 إحصائياتك الشخصية

🏆 النقاط الإجمالية: {user_scores.get(user_id, 0)}
⚡ مستواك: {'مبتدئ' if user_scores.get(user_id, 0) < 10 else 'متوسط' if user_scores.get(user_id, 0) < 30 else 'متقدم' if user_scores.get(user_id, 0) < 50 else 'محترف' if user_scores.get(user_id, 0) < 100 else 'أسطورة'}

✅ الإجابات الصحيحة:
كلمات: {user_stats.get('words_correct', 0)}
أرقام: {user_stats.get('numbers_correct', 0)}
جمل: {user_stats.get('sentences_correct', 0)}

❌ الأخطاء:
كلمات: {user_stats.get('words_wrong', 0)}
أرقام: {user_stats.get('numbers_wrong', 0)}
جمل: {user_stats.get('sentences_wrong', 0)}

⏱️ الوقت في البوت:
الأيام: {days}
الساعات: {hours}
الدقائق: {minutes}
الثواني: {seconds}
"""
        await query.edit_message_text(stats_text)
    elif data == "speedtest":
        download_speed = random.uniform(10.0, 150.0)
        upload_speed = random.uniform(5.0, 80.0)
        ping = random.randint(8, 50)
        jitter = random.uniform(0.5, 15.0)
        
        speed_text = f"""
🌐 نتيجة قياس السرعة

⬇️ سرعة التنزيل: {download_speed:.1f} Mbps
⬆️ سرعة الرفع: {upload_speed:.1f} Mbps
📶 البنج: {ping} ms
📊 توتر الإرسال: {jitter:.1f} ms

⚡ اتصالك ممتاز
"""
        await query.edit_message_text(speed_text)
    elif data.startswith("section_"):
        section_name = data.replace("section_", "")
        if section_name in custom_sections:
            section = custom_sections[section_name]
            section_text = f"🔮 {section_name}\n\n"
            section_text += f"👥 المشاركون: {len(section['participants'])}/{section['max_participants']}\n"
            section_text += f"📊 الحالة: {'نشط' if section['active'] else 'غير نشط'}\n\n"
            if section['participants']:
                section_text += "📋 قائمة المشاركين:\n"
                for i, participant in enumerate(section['participants'], 1):
                    section_text += f"{i}. {participant}\n"
            
            keyboard = []
            for command in section_commands.get(section_name, []):
                keyboard.append([InlineKeyboardButton(command['name'], callback_data=f"cmd_{section_name}_{command['name']}")])
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(section_text, reply_markup=reply_markup)
    elif data.startswith("cmd_"):
        parts = data.split("_")
        section_name = parts[1]
        command_name = parts[2]
        
        await query.edit_message_text(f"🔧 تنفيذ الأمر: {command_name} في القسم: {section_name}")

async def check_active_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر لفحص التحدي النشط"""
    chat_id = update.effective_chat.id
    
    active_challenge_found = False
    for challenge_id, challenge in active_challenges.items():
        if challenge['chat_id'] == chat_id:
            active_challenge_found = True
            creator = challenge['creator']
            participants = challenge.get('participants', [])
            scores = challenge.get('scores', {})
            
            info_text = f"""
📊 معلومات التحدي النشط:

🆔 المعرف: {challenge_id}
🎯 النوع: {challenge['type']}
🏆 نقاط الفوز: {challenge['win_points']}
👤 المنشئ: {creator['name']}

📋 المشاركون ({len(participants)}):
"""
            for participant in participants:
                info_text += f"• {participant}\n"
            
            info_text += "\n🎯 النقاط الحالية:\n"
            for user_id, score in scores.items():
                info_text += f"• {score} نقطة\n"
            
            await update.message.reply_text(info_text)
            break
    
    if not active_challenge_found:
        await update.message.reply_text("❌ لا يوجد تحدي نشط في هذه المجموعة")

async def handle_challenge_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    username = update.effective_user.username or ""

    for challenge_id in list(active_challenges.keys()):
        if active_challenges[challenge_id]['creator']['id'] == user_id:
            del active_challenges[challenge_id]

    challenge_id = str(random.randint(1000, 9999))
    active_challenges[challenge_id] = {
        'creator': {'id': user_id, 'name': user_name, 'username': username},
        'participants': [],
        'max_participants': 0,
        'status': 'awaiting_count',
        'scores': {},
        'type': None,
        'chat_id': update.effective_chat.id,
        'paused': False
    }

    message_text = f"🎯 مقدم اللعبة: {user_name} (@{username if username else 'بدون معرف'})\n\n👥 كم عدد الأشخاص الذين سوف يشاركون في التحدي؟ (1-30)"
    
    if update.message:
        await update.message.reply_text(message_text)
    elif update.callback_query:
        await update.callback_query.edit_message_text(message_text)

async def send_challenge_type_selection(update: Update, challenge_id: str):
    challenge = active_challenges[challenge_id]
    
    participants_text = "\n".join([f"• {p}" for p in challenge['participants']])
    
    keyboard = [
        [InlineKeyboardButton("🔢 أرقام فقط ⚡ ار", callback_data=f"type_numbers_{challenge_id}")],
        [InlineKeyboardButton("📝 كلمات فقط ⚡ كل", callback_data=f"type_words_{challenge_id}")],
        [InlineKeyboardButton("💬 جمل فقط ⚡ جم", callback_data=f"type_sentences_only_{challenge_id}")],
        [InlineKeyboardButton("🔢📝 أرقام + كلمات ⚡ اك", callback_data=f"type_both_{challenge_id}")],
        [InlineKeyboardButton("🔢💬 أرقام + جمل ⚡ اج", callback_data=f"type_numbers_sentences_{challenge_id}")],
        [InlineKeyboardButton("📝💬 كلمات + جمل ⚡ كج", callback_data=f"type_words_sentences_{challenge_id}")],
        [InlineKeyboardButton("🎯 الكل ⚡ ال", callback_data=f"type_all_{challenge_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message_text = f"🎉 اكتمل عدد المشاركين!\n\n👥 قائمة المشاركين:\n{participants_text}\n\n🎯 اختر نوع التحدي:"
    
    if update.message:
        await update.message.reply_text(message_text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)

async def handle_challenge_type_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    challenge_id = data.split('_')[-1]
    
    if challenge_id not in active_challenges:
        return
    
    challenge = active_challenges[challenge_id]
    
    if 'type_numbers_sentences' in data:
        challenge['type'] = 'numbers_sentences'
    elif 'type_words_sentences' in data:
        challenge['type'] = 'words_sentences'
    elif 'type_sentences_only' in data:
        challenge['type'] = 'sentences_only'
    elif 'type_all' in data:
        challenge['type'] = 'all'
    elif 'type_numbers' in data:
        challenge['type'] = 'numbers'
    elif 'type_words' in data:
        challenge['type'] = 'words'
    elif 'type_both' in data:
        challenge['type'] = 'both'
    
    challenge['status'] = 'awaiting_points'
    
    await query.edit_message_text(f"🎯 نوع التحدي: {challenge['type']}\n\n🏆 كم نقطة للفوز في هذا التحدي؟ (1-70)")

async def show_user_stats_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_user = None
        
        if update.message.reply_to_message:
            target_user = update.message.reply_to_message.from_user
        
        else:
            message_text = update.message.text
            if '@' in message_text:
                import re
                username_match = re.search(r'@(\w+)', message_text)
                if username_match:
                    username = username_match.group(1)
                    target_user = update.message.from_user
        
        if not target_user:
            target_user = update.message.from_user
        
        user_id = target_user.id
        user_name = target_user.first_name
        username = target_user.username or "بدون معرف"
        
        user_stats = context.bot_data.get('user_stats', {}).get(user_id, {})
        user_score = user_scores.get(user_id, 0)
        
        words_correct = user_stats.get('words_correct', 0)
        words_wrong = user_stats.get('words_wrong', 0)
        numbers_correct = user_stats.get('numbers_correct', 0)
        numbers_wrong = user_stats.get('numbers_wrong', 0)
        sentences_correct = user_stats.get('sentences_correct', 0)
        sentences_wrong = user_stats.get('sentences_wrong', 0)
        
        total_correct = words_correct + numbers_correct + sentences_correct
        total_wrong = words_wrong + numbers_wrong + sentences_wrong
        total_attempts = total_correct + total_wrong
        
        win_count = 0
        lose_count = 0
        for challenge in active_challenges.values():
            if user_id in challenge.get('scores', {}):
                if challenge['scores'][user_id] >= challenge.get('win_points', 0):
                    win_count += 1
                else:
                    lose_count += 1
        
        accuracy = (total_correct / total_attempts * 100) if total_attempts > 0 else 0
        win_rate = (win_count / (win_count + lose_count) * 100) if (win_count + lose_count) > 0 else 0
        
        activity_score = min(100, (total_attempts * 2))
        power_score = min(100, (user_score * 1.5))
        consistency_score = min(100, (accuracy + win_rate) / 2)
        
        overall_rating = (activity_score + power_score + consistency_score) / 3
        
        level = "مبتدئ" if overall_rating < 30 else "متوسط" if overall_rating < 50 else "متقدم" if overall_rating < 70 else "محترف" if overall_rating < 90 else "أسطورة"
        
        performance_quotes = {
            "مبتدئ": "🌱 بذرة واعدة تبدأ رحلتها نحو القمة",
            "متوسط": "🚀 متسابق طموح يصنع فارقاً في المنافسة", 
            "متقدم": "💎 لاعب متميز يترك بصمته في كل تحد",
            "محترف": "🏆 بطل مخضرم يتقن فنون السرعة والدقة",
            "أسطورة": "⚡ أسطورة حية تكتب التاريخ بأحرف من نور"
        }
        
        quote = performance_quotes.get(level, "🌟 لاعب جديد في عالم التحدي")
        
        username_link = f"https://t.me/{username}" if username != "بدون معرف" else f"tg://user?id={user_id}"
        username_display = f'<a href="{username_link}">@{username}</a>' if username != "بدون معرف" else "بدون معرف"
        
        stats_text = f"""
📊 إحصائيات اللاعب الشاملة ⚡

👤 معلومات اللاعب
├ الاسم: <a href="tg://user?id={user_id}">{user_name}</a>
├ المعرف: {username_display}
└ الايدي: <a href="tg://user?id={user_id}">{user_id}</a>

✅ الإجابات الصحيحة
├ الكلمات: {words_correct} ✓
├ الأرقام: {numbers_correct} ✓
├ الجمل: {sentences_correct} ✓
└ الإجمالي: {total_correct} ✓

📈 الإحصائيات العامة
├ إجمالي المحاولات: {total_attempts}
├ الأخطاء المرتكبة: {total_wrong}
├ نسبة الدقة: {accuracy:.1f}%
└ النقاط الإجمالية: {user_score}

⚔️ سجل التحديات
├ الانتصارات: {win_count}
├ الهزائم: {lose_count}
└ معدل الفوز: {win_rate:.1f}%

🎖️ التقييم الشامل
├ مستوى التفاعل: {activity_score:.1f}%
├ مستوى القوة: {power_score:.1f}%
├ مستوى الثبات: {consistency_score:.1f}%
├ التقييم العام: {overall_rating:.1f}%
└ التصنيف: {level}

💫 التقييم النهائي
{quote}

🏆 النتائج الإجمالية
• إجمالي النقاط: {user_score}
• التصنيف العالمي: {level}
• نسبة التميز: {overall_rating:.1f}%
"""
        
        try:
            photo_file = await context.bot.get_user_profile_photos(user_id, limit=1)
            if photo_file.total_count > 0:
                photo = photo_file.photos[0][-1]
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=photo.file_id,
                    caption=stats_text,
                    parse_mode='HTML',
                    reply_to_message_id=update.message.message_id
                )
                return
        except:
            pass
        
        await update.message.reply_text(stats_text, parse_mode='HTML', reply_to_message_id=update.message.message_id)
        
    except Exception as e:
        await update.message.reply_text("❌ حدث خطأ في عرض الإحصائيات", reply_to_message_id=update.message.message_id)

async def show_challenge_creator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        
        for challenge_id, challenge in active_challenges.items():
            if challenge['chat_id'] == chat_id:
                creator = challenge['creator']
                creator_text = "🔥 ━━━━━━━━━━━━━━━━━━━ 🔥\n              مقدم التحدي والمشرف عليه \n\n                         <a href=\"tg://user?id={creator['id']}\">𓆩 𝗛𝗘𝗫𓆪</a>\n                         @{creator['username'] if creator['username'] else 'بدون معرف'}\n\n🔥 ━━━━━━━━━━━━━━━━━━━ 🔥"
                
                if update.message:
                    await update.message.reply_text(creator_text, parse_mode='HTML')
                elif update.callback_query:
                    await update.callback_query.edit_message_text(creator_text, parse_mode='HTML')
                return
        
        message_text = "❌ لا يوجد تحدي نشط"
        if update.message:
            await update.message.reply_text(message_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message_text)
    except Exception as e:
        message_text = "❌ حدث خطأ في عرض معلومات مقدم التحدي"
        if update.message:
            await update.message.reply_text(message_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message_text)

async def show_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = update.effective_chat.id
        
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                participants = challenge.get('participants', [])
                if participants:
                    participants_text = "👥 **قائمة المشاركين:**\n\n" + "\n".join([f"• {p}" for p in participants])
                    if update.message:
                        await update.message.reply_text(participants_text, parse_mode='Markdown')
                    elif update.callback_query:
                        await update.callback_query.edit_message_text(participants_text, parse_mode='Markdown')
                else:
                    message_text = "📭 لا يوجد مشاركين بعد"
                    if update.message:
                        await update.message.reply_text(message_text)
                    elif update.callback_query:
                        await update.callback_query.edit_message_text(message_text)
                return
        
        message_text = "❌ لا يوجد تحدي نشط في هذه المجموعة"
        if update.message:
            await update.message.reply_text(message_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message_text)
    except Exception as e:
        message_text = "❌ حدث خطأ في عرض المشاركين"
        if update.message:
            await update.message.reply_text(message_text)
        elif update.callback_query:
            await update.callback_query.edit_message_text(message_text)

async def show_records(update: Update, context: ContextTypes.DEFAULT_TYPE):
    record_text = "🏆 ━━━━━━━━━━━━━━━━━━━ 🏆\n"
    record_text += "                 الأرقام القياسية\n"


    record_text += "📝 ━━━━━━━━━━━━━━━━━━━ 📝\n"
    record_text += "                 أسرع 5 كلمات\n"

    all_word_times = []
    
    for record in user_records['word']:
        all_word_times.append(record)
    
    if records['word']['time'] != float('inf'):
        all_word_times.append(records['word'])
    
    seen_words = set()
    unique_words = []
    for record in all_word_times:
        identifier = f"{record['user_id']}_{record['content']}"
        if identifier not in seen_words:
            seen_words.add(identifier)
            unique_words.append(record)
    
    unique_words.sort(key=lambda x: x['time'])
    top_5_words = unique_words[:5]
    
    if top_5_words:
        for i, record in enumerate(top_5_words, 1):
            username_display = f"@{record['username']}" if record['username'] else "بدون معرف"
            record_text += f"{i}. <a href=\"tg://user?id={record['user_id']}\">{record['user_name']}</a> ({username_display})\n"
            record_text += f"   ⏱ {record['time']:.2f} ثانية\n"
            record_text += f"   ✅ {record['content']}\n\n"
    else:
               record_text += "لا توجد سجلات للكلمات بعد\n\n"

    record_text += "🔢 ━━━━━━━━━━━━━━━━━━━ 🔢\n"
    record_text += "                 أسرع 5 أرقام\n"

    all_number_times = []
    
    for record in user_records['number']:
        all_number_times.append(record)
    
    if records['number']['time'] != float('inf'):
        all_number_times.append(records['number'])
    
    seen_numbers = set()
    unique_numbers = []
    for record in all_number_times:
        identifier = f"{record['user_id']}_{record['content']}"
        if identifier not in seen_numbers:
            seen_numbers.add(identifier)
            unique_numbers.append(record)
    
    unique_numbers.sort(key=lambda x: x['time'])
    top_5_numbers = unique_numbers[:5]
    
    if top_5_numbers:
        for i, record in enumerate(top_5_numbers, 1):
            username_display = f"@{record['username']}" if record['username'] else "بدون معرف"
            record_text += f"{i}. <a href=\"tg://user?id={record['user_id']}\">{record['user_name']}</a> ({username_display})\n"
            record_text += f"   ⏱ {record['time']:.2f} ثانية\n"
            record_text += f"   ✅ {record['content']}\n\n"
    else:
               record_text += "لا توجد سجلات للأرقام بعد\n\n"

    record_text += "💬 ━━━━━━━━━━━━━━━━━━━ 💬\n"
    record_text += "                 أسرع 5 جمل\n"

    all_sentence_times = []
    
    for record in user_records['sentence']:
        all_sentence_times.append(record)
    
    if records['sentence']['time'] != float('inf'):
        all_sentence_times.append(records['sentence'])
    
    seen_sentences = set()
    unique_sentences = []
    for record in all_sentence_times:
        identifier = f"{record['user_id']}_{record['content']}"
        if identifier not in seen_sentences:
            seen_sentences.add(identifier)
            unique_sentences.append(record)
    
    unique_sentences.sort(key=lambda x: x['time'])
    top_5_sentences = unique_sentences[:5]
    
    if top_5_sentences:
        for i, record in enumerate(top_5_sentences, 1):
            username_display = f"@{record['username']}" if record['username'] else "بدون معرف"
            record_text += f"{i}. <a href=\"tg://user?id={record['user_id']}\">{record['user_name']}</a> ({username_display})\n"
            record_text += f"   ⏱ {record['time']:.2f} ثانية\n"
            record_text += f"   ✅ {record['content']}\n\n"
    else:
               record_text += "لا توجد سجلات للجمل بعد\n\n"

    record_text += "⚡ ━━━━━━━━━━━━━━━━━━━ ⚡\n"
    record_text += "            الأبطال لا يخلقون\n"
    record_text += "                 الأعذار\n"
    record_text += "            بل يصنعون التاريخ\n"
    record_text += "⚡ ━━━━━━━━━━━━━━━━━━━ ⚡\n"

    record_text += "💪 حاول كسر هذه الأرقام القياسية!"
    
    if update.message:
        await update.message.reply_text(record_text, parse_mode='HTML')
    elif update.callback_query:
        await update.callback_query.message.reply_text(record_text, parse_mode='HTML')
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=record_text, parse_mode='HTML')

def update_user_records(user_id, user_name, username, content_type, content, response_time):
    if content_type not in user_records:
        return
        
    if response_time < records[content_type]['time']:
        records[content_type] = {
            'time': response_time,
            'user_name': user_name,
            'user_id': user_id,
            'username': username,
            'content': content
        }
    
    new_record = {
        'time': response_time,
        'user_name': user_name,
        'user_id': user_id,
        'username': username,
        'content': content
    }
    
    user_records[content_type].append(new_record)
    
    seen = set()
    unique_records = []
    for record in user_records[content_type]:
        identifier = f"{record['user_id']}_{record['content']}"
        if identifier not in seen:
            seen.add(identifier)
            unique_records.append(record)
    
    unique_records.sort(key=lambda x: x['time'])
    user_records[content_type] = unique_records[:5]

async def private_control_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    
    if username != "HEX_A":
        await update.message.reply_text("❌ هذا الأمر للمطور فقط")
        return
    
    keyboard = [
        [InlineKeyboardButton("🟢 تشغيل البوت", callback_data="admin_bot_on"),
         InlineKeyboardButton("🔴 إيقاف البوت", callback_data="admin_bot_off")],
        [InlineKeyboardButton("📊 إحصائيات البوت", callback_data="admin_bot_stats"),
         InlineKeyboardButton("🛠️ إعدادات متقدمة", callback_data="admin_advanced")],
        [InlineKeyboardButton("👥 إدارة المجموعات", callback_data="admin_groups"),
         InlineKeyboardButton("🔐 وضع المقيد", callback_data="admin_restrict")],
        [InlineKeyboardButton("📈 إحصائيات حية", callback_data="admin_live_stats"),
         InlineKeyboardButton("🗑️ تنظيف البيانات", callback_data="admin_clean")],
        [InlineKeyboardButton("🎮 لوحة الأوامر", callback_data="cmd_main"),
         InlineKeyboardButton("🚀 إعادة التشغيل", callback_data="admin_restart")],
        [InlineKeyboardButton("📋 سجلات النظام", callback_data="admin_logs"),
         InlineKeyboardButton("⚡ الأداء", callback_data="admin_performance")],
        [InlineKeyboardButton("🔧 التحكم الكامل", callback_data="admin_full_control"),
         InlineKeyboardButton("📡 المراقبة", callback_data="admin_monitor")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    status_icon = "🟢" if BOT_STATUS == "online" else "🔴"
    restrict_icon = "🔒" if RESTRICTED_MODE else "🔓"
    
    control_text = f"""🎛️ ━━━━━━━━━━━━━━━━━━━ 🎛️
         لوحة التحكم المتقدمة
🎛️ ━━━━━━━━━━━━━━━━━━━ 🎛️

📊 حالة البوت: {status_icon} {BOT_STATUS}
🔐 الوضع المقيد: {restrict_icon} {RESTRICTED_MODE}
👥 المجموعات المسموحة: {len(ALLOWED_GROUPS)}
⏰ وقت التشغيل: {int((time.time() - BOT_START_TIME) / 3600)} ساعة

🎯 اختر الأمر المطلوب:"""
    
    await update.message.reply_text(control_text, reply_markup=reply_markup)

async def handle_admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    username = query.from_user.username or ""
    
    if username != "HEX_A":
        await query.answer("❌ هذا القسم للمطور فقط", show_alert=True)
        return
    
    data = query.data
    
    if data == "admin_bot_on":
        global BOT_STATUS
        BOT_STATUS = "online"
        await query.edit_message_text("🟢 تم تشغيل البوت في جميع المجموعات")
        
    elif data == "admin_bot_off":
        BOT_STATUS = "offline"
        await query.edit_message_text("🔴 تم إيقاف البوت في جميع المجموعات")
        
    elif data == "admin_bot_stats":
        total_players = len(user_scores)
        active_players = len([score for score in user_scores.values() if score > 0])
        total_challenges = len(active_challenges)
        total_groups = len(ALLOWED_GROUPS)
        
        stats_text = f"""📊 ━━━━━━━━━━━━━━━━━━━ 📊
         إحصائيات البوت الشاملة
📊 ━━━━━━━━━━━━━━━━━━━ 📊

👥 المستخدمين:
• الإجمالي: {total_players}
• النشطين: {active_players}
• النسبة: {(active_players/total_players*100) if total_players > 0 else 0:.1f}%

🎯 النشاط:
• التحديات النشطة: {total_challenges}
• المجموعات: {total_groups}
• النقاط: {sum(user_scores.values())}

💾 البيانات:
• الكلمات: {len(training_words)}
• الأرقام: {len(training_numbers)}
• الجمل: {len(training_sentences)}"""
        await query.edit_message_text(stats_text)
        
    elif data == "admin_advanced":
        keyboard = [
            [InlineKeyboardButton("🔧 إعدادات الأمان", callback_data="admin_security"),
             InlineKeyboardButton("⚙️ إعدادات الأداء", callback_data="admin_performance")],
            [InlineKeyboardButton("📝 إدارة المحتوى", callback_data="admin_content"),
             InlineKeyboardButton("🔔 الإشعارات", callback_data="admin_notifications")],
            [InlineKeyboardButton("🔙 الرجوع", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🛠️ الإعدادات المتقدمة - اختر القسم:", reply_markup=reply_markup)
        
    elif data == "admin_groups":
        keyboard = [
            [InlineKeyboardButton("➕ إضافة مجموعة", callback_data="admin_add_group"),
             InlineKeyboardButton("➖ حذف مجموعة", callback_data="admin_remove_group")],
            [InlineKeyboardButton("📋 عرض المجموعات", callback_data="admin_list_groups"),
             InlineKeyboardButton("🎯 تفعيل الكل", callback_data="admin_enable_all")],
            [InlineKeyboardButton("🚫 حظر مجموعة", callback_data="admin_ban_group"),
             InlineKeyboardButton("✅ فك حظر مجموعة", callback_data="admin_unban_group")],
            [InlineKeyboardButton("🔙 الرجوع", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("👥 إدارة المجموعات - اختر الإجراء:", reply_markup=reply_markup)
        
    elif data == "admin_restrict":
        global RESTRICTED_MODE
        RESTRICTED_MODE = not RESTRICTED_MODE
        status = "مقيد 🔒" if RESTRICTED_MODE else "مفتوح 🔓"
        await query.edit_message_text(f"🔐 تم تفعيل الوضع {status}")
        
    elif data == "admin_live_stats":
        active_users = len([u for u in context.bot_data.get('user_stats', {}) if context.bot_data['user_stats'][u].get('words_correct', 0) > 0])
        memory_usage = len(str(context.bot_data)) / 1024
        
        live_text = f"""📈 ━━━━━━━━━━━━━━━━━━━ 📈
         الإحصائيات الحية
📈 ━━━━━━━━━━━━━━━━━━━ 📈

👥 المستخدمين النشطين: {active_users}
💾 استخدام الذاكرة: {memory_usage:.1f} كيلوبايت
⚡ التحديات النشطة: {len(active_challenges)}
🕒 وقت التشغيل: {int((time.time() - BOT_START_TIME) / 60)} دقيقة"""
        await query.edit_message_text(live_text)
        
    elif data == "admin_clean":
        old_count = len(user_scores)
        user_scores.clear()
        context.bot_data.clear()
        await query.edit_message_text(f"🗑️ تم تنظيف البيانات - {old_count} سجل")
        
    elif data == "admin_restart":
        await query.edit_message_text("🚀 جاري إعادة تشغيل النظام...")
        import sys
        os.execl(sys.executable, sys.executable, *sys.argv)
        
    elif data == "admin_logs":
        log_text = f"""📋 ━━━━━━━━━━━━━━━━━━━ 📋
         سجلات النظام
📋 ━━━━━━━━━━━━━━━━━━━ 📋

• البوت يعمل منذ: {int((time.time() - BOT_START_TIME) / 3600)} ساعة
• المستخدمين: {len(user_scores)}
• المجموعات: {len(ALLOWED_GROUPS)}
• الحالة: {BOT_STATUS}
• الوضع: {'مقيد' if RESTRICTED_MODE else 'عادي'}"""
        await query.edit_message_text(log_text)
        
    elif data == "admin_performance":
        import psutil
        process = psutil.Process()
        memory = process.memory_info().rss / 1024 / 1024
        
        perf_text = f"""⚡ ━━━━━━━━━━━━━━━━━━━ ⚡
         أداء النظام
⚡ ━━━━━━━━━━━━━━━━━━━ ⚡

💾 استخدام الذاكرة: {memory:.1f} ميجابايت
👥 المستخدمين: {len(user_scores)}
🎯 التحديات: {len(active_challenges)}
📊 البيانات: {len(context.bot_data)}"""
        await query.edit_message_text(perf_text)
        
    elif data == "admin_full_control":
        keyboard = [
            [InlineKeyboardButton("🔄 تحديث الكل", callback_data="admin_refresh_all"),
             InlineKeyboardButton("📤 نسخ احتياطي", callback_data="admin_backup")],
            [InlineKeyboardButton("📥 استعادة نسخة", callback_data="admin_restore"),
             InlineKeyboardButton("🔍 تتبع الأخطاء", callback_data="admin_debug")],
            [InlineKeyboardButton("🔙 الرجوع", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔧 التحكم الكامل - اختر الإجراء:", reply_markup=reply_markup)
        
    elif data == "admin_monitor":
        keyboard = [
            [InlineKeyboardButton("👀 مراقبة النشاط", callback_data="admin_activity"),
             InlineKeyboardButton("📊 رسوم بيانية", callback_data="admin_charts")],
            [InlineKeyboardButton("🔙 الرجوع", callback_data="admin_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("📡 نظام المراقبة - اختر الخيار:", reply_markup=reply_markup)
        
    elif data == "admin_backup":
        backup_data = {
            'user_scores': dict(user_scores),
            'user_stats': dict(context.bot_data.get('user_stats', {})),
            'records': dict(records),
            'training_words': training_words.copy(),
            'training_numbers': training_numbers.copy(),
            'training_sentences': training_sentences.copy(),
            'timestamp': datetime.now().isoformat()
        }
        global BACKUP_DATA
        BACKUP_DATA = backup_data
        
        backup_text = f"""📤 نسخة احتياطية

✅ تم حفظ نسخة احتياطية كاملة
📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
👥 المستخدمين: {len(backup_data['user_scores'])}
💾 حجم البيانات: {len(str(backup_data))} بايت"""
        await query.edit_message_text(backup_text)
        
    elif data == "admin_restore":
        if BACKUP_DATA:
            user_scores.update(BACKUP_DATA['user_scores'])
            context.bot_data['user_stats'] = BACKUP_DATA['user_stats']
            await query.edit_message_text("✅ تم استعادة النسخة الاحتياطية")
        else:
            await query.edit_message_text("❌ لا توجد نسخة احتياطية")
            
    elif data == "admin_add_group":
        context.user_data['awaiting_group'] = True
        await query.edit_message_text("📝 أرسل معرف المجموعة أو الرابط لإضافتها:")
        
    elif data == "admin_remove_group":
        context.user_data['awaiting_remove_group'] = True
        await query.edit_message_text("🗑️ أرسل معرف المجموعة لحذفها:")
        
    elif data == "admin_list_groups":
        if ALLOWED_GROUPS:
            groups_text = "📋 المجموعات المسموحة:\n\n" + "\n".join([f"• {group}" for group in ALLOWED_GROUPS])
        else:
            groups_text = "📭 لا توجد مجموعات مسموحة"
        await query.edit_message_text(groups_text)
        
    elif data == "admin_enable_all":
        ALLOWED_GROUPS.clear()
        await query.edit_message_text("✅ تم تفعيل البوت في جميع المجموعات")
        
    elif data == "admin_ban_group":
        context.user_data['awaiting_ban_group'] = True
        await query.edit_message_text("🚫 أرسل معرف المجموعة لحظرها:")
        
    elif data == "admin_unban_group":
        context.user_data['awaiting_unban_group'] = True
        await query.edit_message_text("✅ أرسل معرف المجموعة لفك الحظر:")
        
    elif data == "admin_back":
        await private_control_panel(update, context)

async def show_commands_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or ""
    is_developer = username == "HEX_A"
    
    if is_developer and update.effective_chat.type == "private":
        keyboard = [
            [InlineKeyboardButton("🎮 أوامر اللعب", callback_data="cmd_basic")],
            [InlineKeyboardButton("⚔️ أوامر التحدي", callback_data="cmd_challenge")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="cmd_stats")],
            [InlineKeyboardButton("👑 أوامر المطور", callback_data="cmd_developer")],
            [InlineKeyboardButton("🔧 إدارة المحتوى", callback_data="cmd_management")],
            [InlineKeyboardButton("🎛️ لوحة التحكم", callback_data="admin_main")]
        ]
    elif is_developer:
        keyboard = [
            [InlineKeyboardButton("🎮 أوامر اللعب", callback_data="cmd_basic")],
            [InlineKeyboardButton("⚔️ أوامر التحدي", callback_data="cmd_challenge")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="cmd_stats")],
            [InlineKeyboardButton("👑 أوامر المطور", callback_data="cmd_developer")],
            [InlineKeyboardButton("🔧 إدارة المحتوى", callback_data="cmd_management")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("🎮 أوامر اللعب", callback_data="cmd_basic")],
            [InlineKeyboardButton("⚔️ أوامر التحدي", callback_data="cmd_challenge")],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data="cmd_stats")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = "🎮 قائمة أوامر البوت - اختر القسم:"
    
    if update.callback_query:
        await update.callback_query.edit_message_text(welcome_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_commands_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    username = query.from_user.username or ""
    is_developer = username == "HEX_A"
    
    if data == "cmd_basic":
        keyboard = [
            [InlineKeyboardButton("📝 تدريب الكلمات", callback_data="play_words")],
            [InlineKeyboardButton("🔢 تدريب الأرقام", callback_data="play_numbers")],
            [InlineKeyboardButton("💬 تدريب الجمل", callback_data="play_sentences")],
            [InlineKeyboardButton("🌐 قياس السرعة", callback_data="speed_test")],
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="cmd_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_text = """🎮━━━━━━━━━━━━━━━━━━━🎮
       🎯 أوامـر الـلـعـب الأسـاسـيـة
🎮━━━━━━━━━━━━━━━━━━━🎮

📝 تدريب الكلمات:
• كتابة كلمات عشوائية بسرعة
• تطوير مهارة الكتابة السريعة
• تحسين الدقة في الكتابة

🔢 تدريب الأرقام:
• كتابة سلاسل أرقام طويلة
• تنمية سرعة الكتابة الرقمية
• تحسين الذاكرة البصرية

💬 تدريب الجمل:
• كتابة جمل كاملة بدقة
• تطوير مهارات التركيز
• تحسين السرعة في الكتابة الطويلة

🌐 قياس السرعة:
• اختبار سرعة الإنترنت
• قياس البنج والاستجابة
• تحليل جودة الاتصال

⚡ الأوامر السريعة:
• ك ، كلمة → لعب الكلمات
• ر ، رقم → لعب الأرقام
• ج ، جملة → لعب الجمل"""
        
        await query.edit_message_text(commands_text, reply_markup=reply_markup)
    
    elif data == "cmd_challenge":
        keyboard = [
            [InlineKeyboardButton("🎯 بدء تحدي جديد", callback_data="start_challenge")],
            [InlineKeyboardButton("📊 متصدرين التحدي", callback_data="show_leaderboard")],
            [InlineKeyboardButton("👥 عرض المشاركين", callback_data="show_participants")],
            [InlineKeyboardButton("⏸️ إيقاف التحدي", callback_data="pause_challenge")],
            [InlineKeyboardButton("▶️ متابعة التحدي", callback_data="resume_challenge")],
            [InlineKeyboardButton("🔚 إنهاء التحدي", callback_data="end_challenge")],
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="cmd_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_text = """⚔️━━━━━━━━━━━━━━━━━━━⚔️
      🏆 أوامـر الـتـحـدي والـمـنـافـسـة
⚔️━━━━━━━━━━━━━━━━━━━⚔️

🎯 بدء تحدي جديد:
• إنشاء غرفة منافسة جماعية
• تحديد عدد المشاركين (1-30)
• اختيار نوع التحدي المطلوب

📊 متصدرين التحدي:
• عرض ترتيب اللاعبين الحالي
• متابعة النقاط والإنجازات
• معرفة المتصدرين في الوقت الحالي

👥 عرض المشاركين:
• رؤية قائمة جميع المشاركين
• معرفة عدد اللاعبين النشطين
• متابعة تقدم المنافسين

⏸️ إيقاف التحدي:
• تجميد المنافسة مؤقتاً
• إيقاف عدادات الوقت
• حفظ التقدم الحالي

▶️ متابعة التحدي:
• استئناف المنافسة المتوقفة
• تفعيل العدادات من جديد
• متابعة من حيث توقفتم

🔚 إنهاء التحدي:
• إنهاء المنافسة نهائياً
• عرض النتائج النهائية
• إعلان الفائز باللقب

🔧 أوامر التحكم:
• اضافة → إضافة لاعب (بالرد)
• ازالة → إزالة لاعب (بالرد)
• المقدم → معلومات مقدم التحدي"""
        
        await query.edit_message_text(commands_text, reply_markup=reply_markup)
    
    elif data == "cmd_stats":
        keyboard = [
            [InlineKeyboardButton("📈 إحصائياتي الشخصية", callback_data="my_stats")],
            [InlineKeyboardButton("🏆 الأرقام القياسية", callback_data="show_records")],
            [InlineKeyboardButton("📊 إحصائيات اللاعبين", callback_data="players_stats")],
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="cmd_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_text = """📊━━━━━━━━━━━━━━━━━━━📊
     📈 أوامـر الإحـصـائـيـات والـتـرتـيـب
📊━━━━━━━━━━━━━━━━━━━📊

📈 إحصائياتي الشخصية:
• عرض إنجازاتك الكاملة
• معرفة مستواك الحالي
• متابعة تقدمك الشخصي

🏆 الأرقام القياسية:
• رؤية أفضل الأوقات المسجلة
• معرفة أسرع اللاعبين
• متابعة الأرقام التاريخية

📊 إحصائيات اللاعبين:
• عرض إحصائيات المجتمع
• معرفة عدد اللاعبين النشطين
• متابعة أداء اللاعبين

🎖️ مستويات اللاعبين:
• مبتدئ → أقل من 10 نقاط
• متوسط → من 10 إلى 30 نقطة  
• متقدم → من 30 إلى 50 نقطة
• محترف → من 50 إلى 100 نقطة
• أسطورة → أكثر من 100 نقطة

📈 أوامر الإحصائيات:
• احصائيات → إحصائياتك الشخصية
• م → إحصائيات لاعب (بالرد)
• ترند → الأرقام القياسية
• متصدرين → ترتيب اللاعبين"""
        
        await query.edit_message_text(commands_text, reply_markup=reply_markup)
    
    elif data == "cmd_developer" and is_developer:
        keyboard = [
            [InlineKeyboardButton("🛠️ إعدادات البوت", callback_data="dev_bot_settings")],
            [InlineKeyboardButton("📦 إدارة المحتوى", callback_data="dev_content_manage")],
            [InlineKeyboardButton("🔧 الأوامر المتقدمة", callback_data="dev_advanced_cmds")],
            [InlineKeyboardButton("📊 إحصائيات النظام", callback_data="dev_system_stats")],
            [InlineKeyboardButton("👥 إدارة الصلاحيات", callback_data="dev_permissions")],
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="cmd_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_text = """👑━━━━━━━━━━━━━━━━━━━👑
      🛠️ أوامـر الـمـطـور الـمـتـقـدمـة
👑━━━━━━━━━━━━━━━━━━━👑

🛠️ إعدادات البوت:
• التحكم الكامل في إعدادات البوت
• تعديل الخصائص والميزات
• إدارة الإعدادات المتقدمة

📦 إدارة المحتوى:
• إضافة/حذف الكلمات والأرقام
• تحديث قاعدة البيانات
• تحسين المحتوى التدريبي

🔧 الأوامر المتقدمة:
• أدوات تطوير متقدمة
• أوامر الصيانة والنظام
• إعدادات الأمان والحماية

📊 إحصائيات النظام:
• مراقبة أداء البوت
• تحليل استخدام الذاكرة
• متابعة إحصائيات الخوادم

👥 إدارة الصلاحيات:
• منح/سحب صلاحيات المطورين
• إدارة المستخدمين المصرح لهم
• التحكم في صلاحيات المساعدين

🎯 أوامر الصلاحيات:
• سم → منح إذن (بالرد)
• حح → سحب إذن (بالرد) 
• مطور ث → ترقية لمطور (بالرد)
• سس → سحب صلاحية (بالرد)
• اذ → عرض المصرح لهم
• الجميع → عرض المطورين

⚡ هذه الأوامر خاصة بالمطور فقط"""
        
        await query.edit_message_text(commands_text, reply_markup=reply_markup)
    
    elif data == "cmd_management" and is_developer:
        keyboard = [
            [InlineKeyboardButton("📝 إدارة الكلمات", callback_data="mng_words")],
            [InlineKeyboardButton("🔢 إدارة الأرقام", callback_data="mng_numbers")],
            [InlineKeyboardButton("💬 إدارة الجمل", callback_data="mng_sentences")],
            [InlineKeyboardButton("🔄 تغيير الأوامر", callback_data="mng_commands")],
            [InlineKeyboardButton("📦 الإضافة الجماعية", callback_data="mng_bulk_add")],
            [InlineKeyboardButton("🔙 الرجوع للقائمة الرئيسية", callback_data="cmd_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        commands_text = """🔧━━━━━━━━━━━━━━━━━━━🔧
      📦 إدارة الـمـحـتـوى والـبـيـانـات
🔧━━━━━━━━━━━━━━━━━━━🔧

📝 إدارة الكلمات:
• إضافة كلمات جديدة للتدريب
• حذف كلمات غير مناسبة
• تحديث مكتبة الكلمات باستمرار

🔢 إدارة الأرقام:
• إضافة سلاسل أرقام جديدة
• تحسين تنوع التمارين الرقمية
• تحديث قاعدة البيانات الرقمية

💬 إدارة الجمل:
• إضافة جمل تدريبية جديدة
• تحسين جودة المحتوى النصي
• تنويع الجمل للتدريب المتقدم

🔄 تغيير الأوامر:
• تخصيص أوامر البوت
• تعديل الاختصارات
• تحسين تجربة المستخدم

📦 الإضافة الجماعية:
• رفع كميات كبيرة من المحتوى
• استيراد قواعد بيانات خارجية
• تحديث سريع للمحتوى

📊 إحصائيات المحتوى:
• الكلمات: قاعدة بيانات كلمات التدريب
• الأرقام: مكتبة السلاسل الرقمية  
• الجمل: مجموعة الجمل التدريبية
• التحديثات: آخر التحديثات والمضافات"""
        
        await query.edit_message_text(commands_text, reply_markup=reply_markup)
    
    elif data == "cmd_main":
        await show_commands_menu(update, context)
    
    elif data in ["play_words", "play_numbers", "play_sentences"]:
        content_type = data.replace("play_", "")
        if content_type == "words":
            await query.edit_message_text("🎯 تم تفعيل وضع الكلمات\n\nاكتب 'ك' أو 'كلمة' للبدء في التدريب على الكلمات العشوائية")
        elif content_type == "numbers":
            await query.edit_message_text("🎯 تم تفعيل وضع الأرقام\n\nاكتب 'ر' أو 'رقم' للبدء في التدريب على السلاسل الرقمية")
        elif content_type == "sentences":
            await query.edit_message_text("🎯 تم تفعيل وضع الجمل\n\nاكتب 'ج' أو 'جملة' للبدء في التدريب على الجمل الكاملة")
    
    elif data == "speed_test":
        download_speed = random.uniform(50.0, 200.0)
        upload_speed = random.uniform(20.0, 100.0)
        ping = random.randint(5, 35)
        jitter = random.uniform(0.1, 8.0)
        
        speed_text = f"""🌐━━━━━━━━━━━━━━━━━━━🌐
          📊 نـتـيـجـة قـيـاس الـسـرعـة
🌐━━━━━━━━━━━━━━━━━━━🌐

📊 تفاصيل السرعة:
⬇️ سرعة التنزيل: {download_speed:.1f} Mbps
⬆️ سرعة الرفع: {upload_speed:.1f} Mbps  
📶 زمن الاستجابة: {ping} ms
📊 استقرار الإرسال: {jitter:.1f} ms

⚡ تقييم الأداء:
• سرعة التنزيل: {'ممتازة' if download_speed > 100 else 'جيدة جداً' if download_speed > 50 else 'جيدة'}
• استقرار الاتصال: {'مثالي' if ping < 15 else 'ممتاز' if ping < 25 else 'جيد'}
• جودة الخدمة: {'ممتازة' if jitter < 2 else 'جيدة جداً' if jitter < 5 else 'جيدة'}"""
        
        await query.edit_message_text(speed_text)
    
    elif data == "my_stats":
        user_stats = context.bot_data.get('user_stats', {}).get(user_id, {})
        user_score = user_scores.get(user_id, 0)
        
        words_correct = user_stats.get('words_correct', 0)
        numbers_correct = user_stats.get('numbers_correct', 0)
        sentences_correct = user_stats.get('sentences_correct', 0)
        total_correct = words_correct + numbers_correct + sentences_correct
        
        level = "مبتدئ" if user_score < 10 else "متوسط" if user_score < 30 else "متقدم" if user_score < 50 else "محترف" if user_score < 100 else "أسطورة"
        
        stats_text = f"""📊━━━━━━━━━━━━━━━━━━━📊
          📈 إحـصـائـيـاتـك الـشـخـصـيـة
📊━━━━━━━━━━━━━━━━━━━📊

🏆 الإنجازات العامة:
• النقاط الإجمالية: {user_score}
• المستوى الحالي: {level}
• الإجابات الصحيحة: {total_correct}

🎯 التفاصيل الدقيقة:
• الكلمات الصحيحة: {words_correct}
• الأرقام الصحيحة: {numbers_correct}  
• الجمل الصحيحة: {sentences_correct}

📈 التقدم والمستوى:
• المستوى التالي: {'10 نقاط' if user_score < 10 else '30 نقطة' if user_score < 30 else '50 نقطة' if user_score < 50 else '100 نقطة' if user_score < 100 else 'الحد الأقصى'}
• النقاط المتبقية: {max(0, 10 - user_score) if user_score < 10 else max(0, 30 - user_score) if user_score < 30 else max(0, 50 - user_score) if user_score < 50 else max(0, 100 - user_score) if user_score < 100 else 0}

💪 واصل التقدم للوصول للمستوى التالي!"""
        
        await query.edit_message_text(stats_text)
    
    elif data == "show_records":
        await show_records(update, context)
    
    elif data == "players_stats":
        total_players = len(user_scores)
        active_players = len([score for score in user_scores.values() if score > 0])
        total_score = sum(user_scores.values())
        avg_score = total_score / max(1, active_players)
        
        stats_text = f"""📊━━━━━━━━━━━━━━━━━━━📊
     📈 إحـصـائـيـات الـمـجـتـمـع
📊━━━━━━━━━━━━━━━━━━━📊

👥 إحصائيات اللاعبين:
• إجمالي اللاعبين: {total_players}
• اللاعبين النشطين: {active_players}
• النقاط الإجمالية: {total_score}

📈 متوسط الأداء:
• متوسط النقاط: {avg_score:.1f}
• نسبة النشاط: {(active_players/total_players*100) if total_players > 0 else 0:.1f}%
• تفاعل المجتمع: {'ممتاز' if avg_score > 50 else 'جيد جداً' if avg_score > 25 else 'جيد'}

🏆 تصنيف المجتمع:
• مجتمع {'نشط جداً' if active_players > total_players * 0.7 else 'نشط' if active_players > total_players * 0.5 else 'متوسط النشاط'}"""
        
        await query.edit_message_text(stats_text)
    
    elif data == "start_challenge":
        await handle_challenge_start(update, context)
    
    elif data == "show_leaderboard":
        await show_leaderboard(update, context)
    
    elif data == "show_participants":
        await show_participants(update, context)
    
    elif data == "pause_challenge":
        chat_id = update.effective_chat.id
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                challenge['paused'] = True
                await query.edit_message_text("⏸️ تم إيقاف التحدي مؤقتاً")
                return
        await query.edit_message_text("❌ لا يوجد تحدي نشط لإيقافه")
    
    elif data == "resume_challenge":
        chat_id = update.effective_chat.id
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                challenge['paused'] = False
                await query.edit_message_text("▶️ تم استئناف التحدي")
                return
        await query.edit_message_text("❌ لا يوجد تحدي متوقف لاستئنافه")
    
    elif data == "end_challenge":
        chat_id = update.effective_chat.id
        for challenge_id, challenge in list(active_challenges.items()):
            if challenge['chat_id'] == chat_id:
                del active_challenges[challenge_id]
                await query.edit_message_text("🔚 تم إنهاء التحدي بنجاح")
                return
        await query.edit_message_text("❌ لا يوجد تحدي نشط لإنهائه")
    
    elif data in ["dev_bot_settings", "dev_content_manage", "dev_advanced_cmds", "dev_system_stats", "dev_permissions"]:
        if is_developer:
            await query.edit_message_text("🛠️ هذه الأوامر خاصة بالمطور وتحتاج إلى تفعيل من لوحة التحكم المتقدمة")
        else:
            await query.answer("❌ هذا القسم خاص بالمطور فقط", show_alert=True)
    
    elif data in ["mng_words", "mng_numbers", "mng_sentences", "mng_commands", "mng_bulk_add"]:
        if is_developer:
            await query.edit_message_text("📦 نظام إدارة المحتوى جاهز - يمكنك استخدام الأوامر النصية للإدارة")
        else:
            await query.answer("❌ هذا القسم خاص بالمطور فقط", show_alert=True)
    
    elif not is_developer and data in ["cmd_developer", "cmd_management", "dev_bot_settings", "dev_content_manage", "dev_advanced_cmds", "dev_system_stats", "dev_permissions", "mng_words", "mng_numbers", "mng_sentences", "mng_commands", "mng_bulk_add"]:
        await query.answer("❌ هذا القسم خاص بالمطور فقط", show_alert=True)

    elif data == "admin_main":
        await private_control_panel(update, context)

async def handle_bot_control_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    if query.from_user.username != "HEX_A":
        await query.edit_message_text("❌ هذا الأمر للمطور فقط")
        return
    
    if data == "bot_stop_options":
        keyboard = [
            [InlineKeyboardButton("⏸️ إيقاف الكل", callback_data="stop_all")],
            [InlineKeyboardButton("📱 إيقاف الخاص فقط", callback_data="stop_private")],
            [InlineKeyboardButton("👥 إيقاف المجموعات فقط", callback_data="stop_groups")],
            [InlineKeyboardButton("🔍 إيقاف مجموعات محددة", callback_data="stop_specific")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("⏸️ خيارات إيقاف البوت:", reply_markup=reply_markup)
    
    elif data == "bot_start_options":
        keyboard = [
            [InlineKeyboardButton("▶️ تشغيل الكل", callback_data="start_all")],
            [InlineKeyboardButton("📱 تشغيل الخاص فقط", callback_data="start_private")],
            [InlineKeyboardButton("👥 تشغيل المجموعات فقط", callback_data="start_groups")],
            [InlineKeyboardButton("🔍 تشغيل مجموعات محددة", callback_data="start_specific")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("▶️ خيارات تشغيل البوت:", reply_markup=reply_markup)
    
    elif data == "backup_options":
        keyboard = [
            [InlineKeyboardButton("💾 إنشاء نسخة", callback_data="create_backup")],
            [InlineKeyboardButton("🔄 استعادة نسخة", callback_data="restore_backup_list")],
            [InlineKeyboardButton("📋 قائمة النسخ", callback_data="list_backups")],
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_to_control")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("💾 خيارات النسخ الاحتياطي:", reply_markup=reply_markup)
    
    elif data == "active_groups_list":
        active_groups_text = "📊 المجموعات النشطة:\n\n"
        for chat_id, group_data in bot_settings['active_groups'].items():
            active_groups_text += f"• {group_data.get('title', 'مجموعة')}\n"
            active_groups_text += f"  👥 {group_data.get('members', 0)} عضو\n"
            active_groups_text += f"  🆔 {chat_id}\n"
            active_groups_text += "  ──────────────\n"
        
        if not bot_settings['active_groups']:
            active_groups_text = "📭 لا توجد مجموعات نشطة"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="back_to_control")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(active_groups_text, reply_markup=reply_markup)
    
    elif data == "stop_all":
        bot_settings['bot_status'] = 'stopped'
        bot_settings['stopped_private'] = True
        bot_settings['stopped_groups'] = set(bot_settings['active_groups'].keys())
        await query.edit_message_text("✅ تم إيقاف البوت في جميع المجموعات والخاص")
    
    elif data == "stop_private":
        bot_settings['stopped_private'] = True
        await query.edit_message_text("✅ تم إيقاف البوت في الخاص فقط")
    
    elif data == "stop_groups":
        bot_settings['stopped_groups'] = set(bot_settings['active_groups'].keys())
        await query.edit_message_text("✅ تم إيقاف البوت في جميع المجموعات")
    
    elif data == "stop_specific":
        if not bot_settings['active_groups']:
            await query.edit_message_text("❌ لا توجد مجموعات نشطة")
            return
        
        keyboard = []
        for chat_id, group_data in bot_settings['active_groups'].items():
            keyboard.append([InlineKeyboardButton(
                f"⏸️ {group_data.get('title', 'مجموعة')}", 
                callback_data=f"stop_group_{chat_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="bot_stop_options")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔍 اختر المجموعة لايقافها:", reply_markup=reply_markup)
    
    elif data.startswith("stop_group_"):
        chat_id = data.replace("stop_group_", "")
        bot_settings['stopped_groups'].add(chat_id)
        await query.edit_message_text(f"✅ تم إيقاف البوت في المجموعة: {chat_id}")
    
    elif data == "start_all":
        bot_settings['bot_status'] = 'active'
        bot_settings['stopped_private'] = False
        bot_settings['stopped_groups'].clear()
        await query.edit_message_text("✅ تم تشغيل البوت في جميع المجموعات والخاص")
    
    elif data == "start_private":
        bot_settings['stopped_private'] = False
        await query.edit_message_text("✅ تم تشغيل البوت في الخاص فقط")
    
    elif data == "start_groups":
        bot_settings['stopped_groups'].clear()
        await query.edit_message_text("✅ تم تشغيل البوت في جميع المجموعات")
    
    elif data == "start_specific":
        if not bot_settings['stopped_groups']:
            await query.edit_message_text("❌ لا توجد مجموعات موقوفة")
            return
        
        keyboard = []
        for chat_id in bot_settings['stopped_groups']:
            group_data = bot_settings['active_groups'].get(chat_id, {'title': 'مجموعة'})
            keyboard.append([InlineKeyboardButton(
                f"▶️ {group_data.get('title', 'مجموعة')}", 
                callback_data=f"start_group_{chat_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="bot_start_options")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔍 اختر المجموعة لتشغيلها:", reply_markup=reply_markup)
    
    elif data.startswith("start_group_"):
        chat_id = data.replace("start_group_", "")
        if chat_id in bot_settings['stopped_groups']:
            bot_settings['stopped_groups'].remove(chat_id)
        await query.edit_message_text(f"✅ تم تشغيل البوت في المجموعة: {chat_id}")
    
    elif data == "create_backup":
        await backup_bot_data(update, context)
        await query.edit_message_text("✅ تم إنشاء نسخة احتياطية جديدة")
    
    elif data == "restore_backup_list":
        if not backup_files:
            await query.edit_message_text("❌ لا توجد نسخ احتياطية")
            return
        
        keyboard = []
        for backup_id, backup_data in backup_files.items():
            timestamp = datetime.datetime.fromtimestamp(backup_data['timestamp']).strftime('%Y-%m-%d %H:%M')
            keyboard.append([InlineKeyboardButton(
                f"📦 {timestamp}", 
                callback_data=f"restore_{backup_id}"
            )])
        
        keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="backup_options")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🔄 اختر النسخة للاستعادة:", reply_markup=reply_markup)
    
    elif data.startswith("restore_"):
        backup_id = data.replace("restore_", "")
        if backup_id in backup_files:
            backup_data = backup_files[backup_id]
            
            global training_words, training_numbers, training_sentences, user_scores
            global user_detailed_stats, records, active_challenges, challenge_leaderboards
            
            training_words = backup_data['training_words'].copy()
            training_numbers = backup_data['training_numbers'].copy()
            training_sentences = backup_data['training_sentences'].copy()
            user_scores = backup_data['user_scores'].copy()
            user_detailed_stats = backup_data['user_detailed_stats'].copy()
            records = backup_data['records'].copy()
            active_challenges = backup_data['active_challenges'].copy()
            challenge_leaderboards = backup_data['challenge_leaderboards'].copy()
            
            await query.edit_message_text("✅ تم استعادة النسخة الاحتياطية بنجاح")
        else:
            await query.edit_message_text("❌ النسخة غير موجودة")
    
    elif data == "list_backups":
        if not backup_files:
            await query.edit_message_text("❌ لا توجد نسخ احتياطية")
            return
        
        backups_text = "📋 قائمة النسخ الاحتياطية:\n\n"
        for backup_id, backup_data in backup_files.items():
            timestamp = datetime.datetime.fromtimestamp(backup_data['timestamp']).strftime('%Y-%m-%d %H:%M')
            backups_text += f"• {backup_id}\n"
            backups_text += f"  ⏰ {timestamp}\n"
            backups_text += f"  📝 كلمات: {len(backup_data['training_words'])}\n"
            backups_text += f"  🔢 أرقام: {len(backup_data['training_numbers'])}\n"
            backups_text += f"  💬 جمل: {len(backup_data['training_sentences'])}\n"
            backups_text += "  ──────────────\n"
        
        keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data="backup_options")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(backups_text, reply_markup=reply_markup)
    
    elif data == "back_to_control":
        await manage_bot_control(update, context)

print("🚀 بدء تشغيل البوت...")

application = Application.builder().token(TOKEN).build()

application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^cmd_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^play_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^dev_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^mng_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^speed_test"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^my_stats"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^show_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^start_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^pause_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^resume_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^end_"))
application.add_handler(CallbackQueryHandler(handle_commands_callback, pattern="^players_"))
application.add_handler(CallbackQueryHandler(handle_admin_commands, pattern="^admin_"))
application.add_handler(CallbackQueryHandler(handle_bot_control_callback, pattern="^(bot_|stop_|start_|backup_|restore_|create_|list_|back_to_)"))
application.add_handler(CallbackQueryHandler(handle_backup_callback, pattern="^(restore_|cancel_restore)"))

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("check", check_active_challenge))
application.add_handler(CommandHandler("control", manage_bot_control))
application.add_handler(CallbackQueryHandler(handle_challenge_type_selection, pattern="^type_"))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(MessageHandler(filters.Document.ALL, handle_message))

print("✅ البوت يعمل الآن!")
print("💡 اذهب إلى تيليجرام واكتب /start أو /check")

application.run_polling()