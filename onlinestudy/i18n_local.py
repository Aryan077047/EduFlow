"""
Lightweight UI translations for the site shell (en / fa / ps).

Why not Django's django.gettext: the project templates were not built for
blocktrans, and compiling .mo catalogs for three languages on Windows is
out of scope. This table keeps the same behaviour with zero build step --
templates read {{ t.key }} and add new strings by adding dictionary lines.
"""
from django.conf import settings

LANGUAGES = ('en', 'fa', 'ps')

LANGUAGE_NAMES = {
    'en': 'English',
    'fa': 'فارسی (Dari)',
    'ps': 'پښتو (Pashto)',
}

RTL_LANGUAGES = ('fa', 'ps')

# ============================================================
# STRINGS
# ============================================================
# All keys exist in every language; missing keys render as '' rather
# than raising, so adding a template string without its translations can
# never break a page.

T = {
    # ---- shared / header ----
    'search_placeholder': {
        'en': 'Search courses, videos...',
        'fa': 'جستجوی دوره‌ها و ویدیوها...',
        'ps': 'کورسونه او ویډیوګانې پلټنه...',
    },
    'notifications': {
        'en': 'Notifications',
        'fa': 'اعلان‌ها',
        'ps': 'خبرتیاوې',
    },
    'messages': {
        'en': 'Messages',
        'fa': 'پیام‌ها',
        'ps': 'پیغامونه',
    },
    'my_profile': {
        'en': 'My Profile',
        'fa': 'پروفایل من',
        'ps': 'زما پروفایل',
    },
    'my_courses': {
        'en': 'My Courses',
        'fa': 'دوره‌های من',
        'ps': 'زما کورسونه',
    },
    'ai_assistant': {
        'en': 'AI Assistant',
        'fa': 'دستیار هوشمند',
        'ps': 'د AI مرستندوی',
    },
    'logout': {
        'en': 'Logout',
        'fa': 'خروج',
        'ps': 'وتل',
    },
    'login': {
        'en': 'Login',
        'fa': 'ورود',
        'ps': 'ننوتل',
    },
    'student': {
        'en': 'Student',
        'fa': 'شاگرد',
        'ps': 'زده کوونکی',
    },
    'teacher': {
        'en': 'Teacher',
        'fa': 'استاد',
        'ps': 'ښوونکی',
    },

    # ---- setting.html ----
    'back_to_dashboard': {
        'en': 'Back to Dashboard',
        'fa': 'بازگشت به داشبورد',
        'ps': 'بېرته داشبورډ ته',
    },
    'manage_settings': {
        'en': 'Manage appearance, security, and your account.',
        'fa': 'ظاهر، امنیت و حساب خود را مدیریت کنید.',
        'ps': 'بڼه، امنیت او خپل حساب اداره کړئ.',
    },
    'auto_saved': {
        'en': 'Auto-saved',
        'fa': 'به‌طور خودکار ذخیره شد',
        'ps': 'په اتوماتيک ډول خوندي شو',
    },
    'appearance': {
        'en': 'Appearance',
        'fa': 'ظاهر',
        'ps': 'بڼه',
    },
    'dark_mode': {
        'en': 'Dark mode',
        'fa': 'حالت تاریک',
        'ps': 'تور بڼه',
    },
    'dark_mode_hint': {
        'en': 'Switch the interface to a dark color scheme.',
        'fa': 'تغییر رابط کاربری به تم تاریک.',
        'ps': 'انٹرفیس ته د تور رنګ تڼۍ بدل کړئ.',
    },
    'language': {
        'en': 'Language',
        'fa': 'زبان',
        'ps': 'ژبه',
    },
    'language_hint': {
        'en': 'Choose the language for menus and buttons.',
        'fa': 'زبان منوها و دکمه‌ها را انتخاب کنید.',
        'ps': 'د مینوګانو او تڼیو ژبه وټاکئ.',
    },
    'language_saved': {
        'en': 'Language updated.',
        'fa': 'زبان به‌روزرسانی شد.',
        'ps': 'ژبه تازه شوه.',
    },
    'security': {
        'en': 'Security',
        'fa': 'امنیت',
        'ps': 'امنیت',
    },
    'change_password': {
        'en': 'Change password',
        'fa': 'تغییر رمز عبور',
        'ps': 'پټ نوم بدلول',
    },
    'change_password_hint': {
        'en': 'Use a strong password with at least 8 characters.',
        'fa': 'از رمز عبور قوی با حداقل ۸ کاراکتر استفاده کنید.',
        'ps': 'قوي پټ نوم وکاروئ چې لږ تر لږه ۸ توري ولري.',
    },
    'current': {
        'en': 'Current',
        'fa': 'فعلی',
        'ps': 'اوسنی',
    },
    'new': {
        'en': 'New',
        'fa': 'جدید',
        'ps': 'نوی',
    },
    'confirm': {
        'en': 'Confirm',
        'fa': 'تکرار',
        'ps': 'تکرار',
    },
    'new_password_placeholder': {
        'en': 'New password',
        'fa': 'رمز عبور جدید',
        'ps': 'نوی پټ نوم',
    },
    'repeat_password_placeholder': {
        'en': 'Repeat password',
        'fa': 'تکرار رمز عبور',
        'ps': 'پټ نوم تکرار کړئ',
    },
    'cancel': {
        'en': 'Cancel',
        'fa': 'لغو',
        'ps': 'لغوه',
    },
    'update_password': {
        'en': 'Update password',
        'fa': 'به‌روزرسانی رمز',
        'ps': 'پټ نوم تازه کول',
    },
    'danger_zone': {
        'en': 'Danger Zone',
        'fa': 'منطقه خطر',
        'ps': 'د خطر سیمه',
    },
    'delete_account': {
        'en': 'Delete account',
        'fa': 'حذف حساب',
        'ps': 'حساب پاکول',
    },
    'confirm_action_title': {
        'en': 'Are you sure?',
        'fa': 'مطمئن هستید؟',
        'ps': 'ایا ډاډه یاست؟',
    },
    'delete_account_confirm': {
        'en': 'This permanently deletes your account together with your courses, enrollments and comments. This cannot be undone.',
        'fa': 'این کار حساب شما را به همراه دوره‌ها، ثبت‌نام‌ها و نظرهایتان برای همیشه حذف می‌کند. این عمل قابل بازگشت نیست.',
        'ps': 'دا ستاسو حساب د کورسونو، ثبتنامونو او تبصرو سره د تل لپاره پاکوي. دا بیرته نه راګرځي.',
    },
    'account_deleted': {
        'en': 'Your account has been deleted. Goodbye!',
        'fa': 'حساب شما حذف شد. خداحافظ!',
        'ps': 'ستاسو حساب پاک شو. خدای پامان!',
    },
    'delete_account_hint': {
        'en': 'This action is permanent and cannot be undone.',
        'fa': 'این عمل دائمی است و قابل بازگشت نیست.',
        'ps': 'دا کار دایمي دی او بېرته نه شي کېدای.',
    },
    'delete': {
        'en': 'Delete',
        'fa': 'حذف',
        'ps': 'پاکول',
    },
    'save_changes': {
        'en': 'Save changes',
        'fa': 'ذخیره تغییرات',
        'ps': 'بدلونونه خوندي کول',
    },

    # ---- login.html ----
    'welcome_back': {
        'en': 'Welcome back!',
        'fa': 'خوش آمدید!',
        'ps': 'بېرته ښه راغلاست!',
    },
    'sign_in_title': {
        'en': 'Sign In',
        'fa': 'ورود',
        'ps': 'ننوتل',
    },
    'sign_in_to_continue': {
        'en': 'Enter your credentials to access your account',
        'fa': 'برای دسترسی به حساب خود وارد شوید',
        'ps': 'خپل حساب ته د لاسرسي لپاره معلومات داخل کړئ',
    },
    'sign_in_subtitle': {
        'en': 'Enter your credentials to continue',
        'fa': 'برای ادامه وارد شوید',
        'ps': 'د دوام لپاره معلومات داخل کړئ',
    },
    'sign_in_left_text': {
        'en': 'Sign in to continue your learning journey with EduFlow.',
        'fa': 'برای ادامه سفر یادگیری با EduFlow وارد شوید.',
        'ps': 'د EduFlow سره د زده کړې سفر دوام لپاره ننوځئ.',
    },
    'password': {
        'en': 'Password',
        'fa': 'رمز عبور',
        'ps': 'پټ نوم',
    },
    'remember_me': {
        'en': 'Remember me',
        'fa': 'مرا به خاطر بسپار',
        'ps': 'ما هېر نه کړه',
    },
    'forgot_password': {
        'en': 'Forgot Password?',
        'fa': 'رمز عبور را فراموش کرده‌اید؟',
        'ps': 'پټ نوم هېر شو؟',
    },
    'no_account': {
        'en': "Don't have an account?",
        'fa': 'حساب ندارید؟',
        'ps': 'حساب نه لرئ؟',
    },
    'create_one_here': {
        'en': 'Create one here',
        'fa': 'همین حالا بسازید',
        'ps': 'دلته جوړ کړئ',
    },

    # ---- shared / general ----
    'dashboard': {
        'en': 'Dashboard', 'fa': 'داشبورد', 'ps': 'ډاشبورډ',
    },
    'home': {
        'en': 'Home', 'fa': 'خانه', 'ps': 'کور',
    },
    'courses': {
        'en': 'Courses', 'fa': 'دوره‌ها', 'ps': 'کورسونه',
    },
    'course': {
        'en': 'Course', 'fa': 'دوره', 'ps': 'کورس',
    },
    'videos': {
        'en': 'Videos', 'fa': 'ویدیوها', 'ps': 'ویډیوګانې',
    },
    'videos_word': {
        'en': 'videos', 'fa': 'ویدیو', 'ps': 'ویډیوګانې',
    },
    'students': {
        'en': 'Students', 'fa': 'شاگردان', 'ps': 'زده کوونکي',
    },
    'teachers': {
        'en': 'Teachers', 'fa': 'اساتید', 'ps': 'ښوونکي',
    },
    'students_word': {
        'en': 'students', 'fa': 'شاگرد', 'ps': 'زده کوونکي',
    },
    'quizzes_word': {
        'en': 'quizzes', 'fa': 'آزمون', 'ps': 'ازموینې',
    },
    'total': {
        'en': 'Total', 'fa': 'مجموع', 'ps': 'ټول',
    },
    'total_word': {
        'en': 'total', 'fa': 'مجموع', 'ps': 'ټول',
    },
    'date': {
        'en': 'Date', 'fa': 'تاریخ', 'ps': 'نېټه',
    },
    'when': {
        'en': 'When', 'fa': 'زمان', 'ps': 'کله',
    },
    'status': {
        'en': 'Status', 'fa': 'وضعیت', 'ps': 'حالت',
    },
    'actions': {
        'en': 'Actions', 'fa': 'عملیات', 'ps': 'کړنې',
    },
    'role': {
        'en': 'Role', 'fa': 'نقش', 'ps': 'رول',
    },
    'active': {
        'en': 'Active', 'fa': 'فعال', 'ps': 'فعال',
    },
    'inactive': {
        'en': 'Inactive', 'fa': 'غیرفعال', 'ps': 'غیر فعال',
    },
    'draft': {
        'en': 'Draft', 'fa': 'پیش‌نویس', 'ps': 'مسوده',
    },
    'published': {
        'en': 'Published', 'fa': 'منتشر شده', 'ps': 'خپاره شوی',
    },
    'publish': {
        'en': 'Publish', 'fa': 'انتشار', 'ps': 'خپرول',
    },
    'edit': {
        'en': 'Edit', 'fa': 'ویرایش', 'ps': 'سمول',
    },
    'view': {
        'en': 'View', 'fa': 'مشاهده', 'ps': 'لیدل',
    },
    'analytics': {
        'en': 'Analytics', 'fa': 'تحلیل‌ها', 'ps': 'شننې',
    },
    'back_to_profile': {
        'en': 'Back to Profile', 'fa': 'بازگشت به پروفایل', 'ps': 'بېرته پروفایل ته',
    },
    'back_to_submissions': {
        'en': 'Back to Submissions', 'fa': 'بازگشت به ارسال‌ها', 'ps': 'بېرته سپارنو ته',
    },
    'back_to_signin': {
        'en': 'Back to sign in', 'fa': 'بازگشت به ورود', 'ps': 'بېرته ننوتلو ته',
    },
    'back_home': {
        'en': 'Back to Home', 'fa': 'بازگشت به خانه', 'ps': 'بېرته کور ته',
    },
    'passed': {
        'en': 'Passed', 'fa': 'قبول', 'ps': 'بریالی',
    },
    'failed': {
        'en': 'Failed', 'fa': 'رد', 'ps': 'ناکام',
    },
    'pending': {
        'en': 'Pending', 'fa': 'در انتظار', 'ps': 'په تمه',
    },
    'points': {
        'en': 'Points', 'fa': 'امتیاز', 'ps': 'ټکي',
    },
    'pts_word': {
        'en': 'pts', 'fa': 'امتیاز', 'ps': 'ټکي',
    },
    'score': {
        'en': 'Score', 'fa': 'نمره', 'ps': 'نمره',
    },
    'submitted_word': {
        'en': 'submitted', 'fa': 'ارسال شده', 'ps': 'سپارل شوی',
    },
    'submitted_label': {
        'en': 'Submitted', 'fa': 'ارسال شده', 'ps': 'سپارل شوی',
    },
    'attempts_word': {
        'en': 'Attempts', 'fa': 'تلاش‌ها', 'ps': 'هڅې',
    },
    'attempt': {
        'en': 'Attempt', 'fa': 'تلاش', 'ps': 'هڅه',
    },
    'enrollments_word': {
        'en': 'Enrollments', 'fa': 'ثبت‌نام‌ها', 'ps': 'نوم لیکنې',
    },
    'enroll_short': {
        'en': 'Enroll.', 'fa': 'ثبت‌نام', 'ps': 'نوم لیکنه',
    },
    'comments_word': {
        'en': 'Comments', 'fa': 'نظرات', 'ps': 'تبصرې',
    },
    'likes_word': {
        'en': 'Likes', 'fa': 'پسندها', 'ps': 'خوښونې',
    },
    'questions_word': {
        'en': 'Questions', 'fa': 'سوالات', 'ps': 'پوښتنې',
    },
    'question_word': {
        'en': 'Question', 'fa': 'سوال', 'ps': 'پوښتنه',
    },
    'of_word': {
        'en': 'of', 'fa': 'از', 'ps': 'له',
    },

    # ---- index.html ----
    'video_courses': {
        'en': 'Video Courses', 'fa': 'دوره‌های ویدیویی', 'ps': 'ویډیو کورسونه',
    },
    'watch_latest': {
        'en': 'Watch latest educational videos', 'fa': 'تازه ویدیوهای آموزشی را ببینید', 'ps': 'وروستې پوهاوي ویډیوګانې وګورئ',
    },
    'watch': {
        'en': 'Watch', 'fa': 'تماشا', 'ps': 'لیدل',
    },
    'instructor': {
        'en': 'Instructor', 'fa': 'مدرس', 'ps': 'ښوونکی',
    },
    'enrolled_btn': {
        'en': '✓ Enrolled', 'fa': '✓ ثبت‌نام شده', 'ps': '✓ نوم لیکل شوی',
    },
    'enroll': {
        'en': 'Enroll', 'fa': 'ثبت‌نام', 'ps': 'نوم لیکنه',
    },
    'no_comments_yet': {
        'en': 'No comments yet. Be the first!', 'fa': 'هنوز نظری نیست. اولین نفر باشید!', 'ps': 'لا تراوسه تبصرې نشته. لومړی یاست!',
    },
    'write_comment': {
        'en': 'Write a comment...', 'fa': 'نظر خود را بنویسید...', 'ps': 'خپله تبصره ولیکه...',
    },
    'send': {
        'en': 'Send', 'fa': 'ارسال', 'ps': 'لېږل',
    },
    'no_courses_yet': {
        'en': 'No courses available yet.', 'fa': 'هنوز دوره‌ای موجود نیست.', 'ps': 'لا تراوسه کورس نشته.',
    },
    'delete_comment_confirm': {
        'en': 'Delete this comment?', 'fa': 'این نظر حذف شود؟', 'ps': 'دا تبصره پاک کړو؟',
    },
    'already_enrolled_alert': {
        'en': 'You are already enrolled in this course!', 'fa': 'شما قبلاً در این دوره ثبت‌نام کرده‌اید!', 'ps': 'تاسو لا دمخه پدې کورس کې نوم لیکلی!',
    },
    # ---- user_profile.html ----
    'course_portfolio': {
        'en': 'Course Portfolio', 'fa': 'سبد دوره‌ها', 'ps': 'کورس پورټفولیو',
    },
    'my_learning': {
        'en': 'My Learning', 'fa': 'یادگیری من', 'ps': 'زما زده کړه',
    },
    'professional_instructor_dashboard': {
        'en': 'Professional instructor dashboard', 'fa': 'داشبورد حرفه‌ای مدرس', 'ps': 'د مسلکي ښوونکي ډاشبورډ',
    },
    'courses_you_enrolled': {
        'en': 'Courses you are enrolled in', 'fa': 'دوره‌هایی که ثبت‌نام کرده‌اید', 'ps': 'هغه کورسونه چې تاسو پکې نوم لیکلی',
    },
    'teacher_application_pending': {
        'en': 'Teacher application pending', 'fa': 'درخواست استاد در انتظار', 'ps': 'د ښوونکي غوښتنه په تمه',
    },
    'approved_teacher': {
        'en': 'Approved teacher', 'fa': 'استاد تأیید شده', 'ps': 'تایید شوی ښوونکی',
    },
    'reapply_teacher': {
        'en': 'Re-apply as Teacher', 'fa': 'درخواست مجدد استاد', 'ps': 'بیا د ښوونکي غوښتنه',
    },
    'apply_teacher': {
        'en': 'Apply as Teacher', 'fa': 'درخواست استاد', 'ps': 'د ښوونکي غوښتنه',
    },
    'create_course': {
        'en': 'Create Course', 'fa': 'ایجاد دوره', 'ps': 'کورس جوړول',
    },
    'personal_info': {
        'en': 'Personal Info', 'fa': 'اطلاعات شخصی', 'ps': 'شخصي معلومات',
    },
    'full_name': {
        'en': 'Full name', 'fa': 'نام کامل', 'ps': 'بشپړ نوم',
    },
    'email_label': {
        'en': 'Email', 'fa': 'ایمیل', 'ps': 'بریښنالیک',
    },
    'member_since': {
        'en': 'Member since', 'fa': 'عضو از', 'ps': 'غړی له',
    },
    'experience': {
        'en': 'Experience', 'fa': 'تجربه', 'ps': 'تجربه',
    },
    'expertise': {
        'en': 'Expertise', 'fa': 'تخصص', 'ps': 'څانګه',
    },
    'not_provided': {
        'en': 'Not provided', 'fa': 'وارد نشده', 'ps': 'نه دی لیکل شوی',
    },
    'portfolio_stats': {
        'en': 'Portfolio stats', 'fa': 'آمار سبد', 'ps': 'پورټفولیو احصایې',
    },
    'learning_stats': {
        'en': 'Learning stats', 'fa': 'آمار یادگیری', 'ps': 'د زده کړې احصایې',
    },
    'enrolled': {
        'en': 'Enrolled', 'fa': 'ثبت‌نام شده', 'ps': 'نوم لیکل شوی',
    },
    'enrolled_students': {
        'en': 'Enrolled students', 'fa': 'شاگردان ثبت‌نام شده', 'ps': 'نوم لیکلي زده کوونکي',
    },
    'my_courses_title': {
        'en': 'My Courses', 'fa': 'دوره‌های من', 'ps': 'زما کورسونه',
    },
    'courses_count_suffix': {
        'en': 'Courses', 'fa': 'دوره', 'ps': 'کورسونه',
    },
    'my_enrolled_courses': {
        'en': 'My Enrolled Courses', 'fa': 'دوره‌های ثبت‌نام شده من', 'ps': 'زما نوم لیکل شوي کورسونه',
    },
    'lessons_word': {
        'en': 'lessons', 'fa': 'درس', 'ps': 'درسونه',
    },
    'you_havent_created_courses': {
        'en': "You haven't created any courses yet.", 'fa': 'هنوز دوره‌ای نساخته‌اید.', 'ps': 'لا تراوسه کورس نه دی جوړ کړی.',
    },
    'playlists_inside_course': {
        'en': 'Playlists and video uploads live inside a course, so create one first.',
        'fa': 'پلی‌لیست‌ها و آپلود ویدیو داخل یک دوره هستند؛ ابتدا یک دوره بسازید.',
        'ps': 'پلې لیستونه او ویډیو پورته کول په یوه کورس کې دي، لومړی یو جوړ کړئ.',
    },
    'create_first_course': {
        'en': 'Create your first course', 'fa': 'اولین دوره خود را بسازید', 'ps': 'خپل لومړی کورس جوړ کړئ',
    },
    'you_havent_enrolled': {
        'en': "You haven't enrolled in any courses yet.", 'fa': 'هنوز در هیچ دوره‌ای ثبت‌نام نکرده‌اید.', 'ps': 'لا تراوسه په هیچ کورس کې نوم نه دی لیکلی.',
    },
    'quiz_btn': {
        'en': 'Quiz', 'fa': 'آزمون', 'ps': 'ازموینه',
    },
    'playlist': {
        'en': 'Playlist', 'fa': 'پلی‌لیست', 'ps': 'پلې لیست',
    },
    'fix_following': {
        'en': 'Please fix the following:', 'fa': 'لطفاً موارد زیر را اصلاح کنید:', 'ps': 'لطف 아 لاندې موں سم کړئ:',
    },
    'course_title': {
        'en': 'Course Title', 'fa': 'عنوان دوره', 'ps': 'د کورس نوم',
    },
    'category': {
        'en': 'Category', 'fa': 'دسته‌بندی', 'ps': 'کټګوري',
    },
    'level': {
        'en': 'Level', 'fa': 'سطح', 'ps': 'کچه',
    },
    'price_label': {
        'en': 'Price ($)', 'fa': 'قیمت ($)', 'ps': 'بیه ($)',
    },
    'video_label': {
        'en': 'Video', 'fa': 'ویدیو', 'ps': 'ویډیو',
    },
    'description': {
        'en': 'Description', 'fa': 'توضیحات', 'ps': 'توضیحات',
    },
    'add_new_course': {
        'en': 'Add New Course', 'fa': 'افزودن دوره جدید', 'ps': 'نوی کورس زیاتول',
    },
    'edit_course': {
        'en': 'Edit Course', 'fa': 'ویرایش دوره', 'ps': 'کورس سمول',
    },
    'keep_current_video': {
        'en': 'Leave empty to keep the current video', 'fa': 'برای حفظ ویدیوی فعلی خالی بگذارید', 'ps': 'اوسنۍ ویډیو ساتلو لپاره تش پرېږدئ',
    },
    'save_changes_btn': {
        'en': 'Save Changes', 'fa': 'ذخیره تغییرات', 'ps': 'بدلونونه خوندي کړئ',
    },
    'create_draft': {
        'en': 'Create Draft', 'fa': 'ایجاد پیش‌نویس', 'ps': 'مسوده جوړول',
    },
    'years_experience': {
        'en': 'Years of Experience', 'fa': 'سال تجربه', 'ps': 'د تجربې کلونه',
    },
    'expertise_area': {
        'en': 'Expertise Area', 'fa': 'حوزه تخصص', 'ps': 'د تخصص سیمه',
    },
    'portfolio_link': {
        'en': 'Portfolio / LinkedIn URL', 'fa': 'لینک نمونه‌کار / لینکدین', 'ps': 'پورټفولیو / د LinkedIn لینک',
    },
    'cv_label': {
        'en': 'CV', 'fa': 'رزومه', 'ps': 'CV',
    },
    'why_teach': {
        'en': 'Why do you want to teach?', 'fa': 'چرا می‌خواهید تدریس کنید؟', 'ps': 'ولې غواړئ تدریس وکړئ؟',
    },
    'submit_application': {
        'en': 'Submit Application', 'fa': 'ارسال درخواست', 'ps': 'غوښتنه سپارل',
    },
    'course_playlist': {
        'en': 'Course Playlist', 'fa': 'پلی‌لیست دوره', 'ps': 'د کورس پلې لیست',
    },
    'now_playing': {
        'en': 'Now Playing', 'fa': 'در حال پخش', 'ps': 'اوس پلې کیږي',
    },
    'total_videos_quizzes': {
        'en': 'Total: 0 videos, 0 quizzes', 'fa': 'مجموع: 0 ویدیو، 0 آزمون', 'ps': 'ټول: ۰ ویډیو، ۰ ازموینې',
    },
    'add_video': {
        'en': 'Add Video', 'fa': 'افزودن ویدیو', 'ps': 'ویډیو زیاتول',
    },
    'only_owner_add': {
        'en': 'Only the course owner can add videos.', 'fa': 'فقط صاحب دوره می‌تواند ویدیو اضافه کند.', 'ps': 'یوازې د کورس خاوند کولی شي ویډیوګانې زیاتې کړي.',
    },
    'no_file_selected': {
        'en': 'No file selected', 'fa': 'فایلی انتخاب نشده', 'ps': 'فایل نه دی ټاکل شوی',
    },
    'upload_video': {
        'en': 'Upload Video', 'fa': 'بارگذاری ویدیو', 'ps': 'ویډیو پورته کول',
    },
    'action_completed': {
        'en': 'Action completed!', 'fa': 'عملیات انجام شد!', 'ps': 'کړنه بشپړه شوه!',
    },

    # ---- dashboard.html (admin) ----
    'admin_panel': {
        'en': 'Admin Panel', 'fa': 'پنل مدیریت', 'ps': 'د ادارې پینل',
    },
    'main_section': {
        'en': 'Main', 'fa': 'اصلی', 'ps': 'اصلي',
    },
    'staff_approval': {
        'en': 'Staff Approval', 'fa': 'تأیید کارکنان', 'ps': 'د کارکوونکو تصویب',
    },
    'content_section': {
        'en': 'Content', 'fa': 'محتوا', 'ps': 'منځپانګه',
    },
    'categories': {
        'en': 'Categories', 'fa': 'دسته‌بندی‌ها', 'ps': 'کټګورۍ',
    },
    'media': {
        'en': 'Media', 'fa': 'رسانه‌ها', 'ps': 'رسنۍ',
    },
    'system_section': {
        'en': 'System', 'fa': 'سیستم', 'ps': 'سیستم',
    },
    'permissions': {
        'en': 'Permissions', 'fa': 'دسترسی‌ها', 'ps': 'اجنې',
    },
    'admin_dashboard_title': {
        'en': 'Admin Dashboard', 'fa': 'داشبورد مدیریت', 'ps': 'د ادارې ډاشبورډ',
    },
    'welcome_back_user': {
        'en': 'Welcome back,', 'fa': 'خوش آمدید،', 'ps': 'بېرته ښه راغلاست،',
    },
    'administrator': {
        'en': 'Administrator', 'fa': 'مدیر', 'ps': 'Administrator',
    },
    'total_courses': {
        'en': 'Total Courses', 'fa': 'مجموع دوره‌ها', 'ps': 'ټول کورسونه',
    },
    'pending_approvals': {
        'en': 'Pending Approvals', 'fa': 'تأییدهای در انتظار', 'ps': 'په تمه تصویبونه',
    },
    'staff_approval_queue': {
        'en': 'Staff Approval Queue', 'fa': 'صف تأیید کارکنان', 'ps': 'د کارکوونکو تصویب قطار',
    },
    'preview_cv': {
        'en': 'Preview CV', 'fa': 'مشاهده رزومه', 'ps': 'CV لیدل',
    },
    'download': {
        'en': 'Download', 'fa': 'دانلود', 'ps': 'ډاونلوډ',
    },
    'no_cv': {
        'en': 'No CV', 'fa': 'بدون رزومه', 'ps': 'CV نشته',
    },
    'approve': {
        'en': 'Approve', 'fa': 'تأیید', 'ps': 'تصویب',
    },
    'reject': {
        'en': 'Reject', 'fa': 'رد', 'ps': 'ردول',
    },
    'all_caught_up': {
        'en': 'All caught up! No pending staff requests.', 'fa': 'همه چیز مرتب است! درخواستی در انتظار نیست.', 'ps': 'هرڅه سم دي! هیڅ غوښتنه په تمه نشته.',
    },
    'all_teachers': {
        'en': 'All Teachers', 'fa': 'همه اساتید', 'ps': 'ټول ښوونکي',
    },
    'add_teacher': {
        'en': 'Add Teacher', 'fa': 'افزودن استاد', 'ps': 'ښوونکی زیاتول',
    },
    'all_students': {
        'en': 'All Students', 'fa': 'همه شاگردان', 'ps': 'ټول زده کوونکي',
    },
    'add_student': {
        'en': 'Add Student', 'fa': 'افزودن شاگرد', 'ps': 'زده کوونکی زیاتول',
    },
    'joined': {
        'en': 'Joined', 'fa': 'عضویت', 'ps': 'غړی شو',
    },
    'add_course': {
        'en': 'Add Course', 'fa': 'افزودن دوره', 'ps': 'کورس زیاتول',
    },
    'all_courses_title': {
        'en': 'All Courses', 'fa': 'همه دوره‌ها', 'ps': 'ټول کورسونه',
    },
    'engagement': {
        'en': 'Engagement', 'fa': 'تعامل', 'ps': 'ګډون',
    },
    'no_teachers_yet': {
        'en': 'No teachers yet.', 'fa': 'هنوز استادی نیست.', 'ps': 'لا تراوسه ښوونکي نشته.',
    },
    'no_students_yet': {
        'en': 'No students yet.', 'fa': 'هنوز شاگردی نیست.', 'ps': 'لا تراوسه زده کوونکي نشته.',
    },
    'no_courses_yet_admin': {
        'en': 'No courses yet.', 'fa': 'هنوز دوره‌ای نیست.', 'ps': 'لا تراوسه کورسونه نشته.',
    },
    'done_toast': {
        'en': 'Done', 'fa': 'انجام شد', 'ps': 'ترسره شو',
    },

    # ---- quiz.html (create quiz) ----
    'create_quiz_title': {
        'en': 'Create a New Quiz', 'fa': 'ایجاد آزمون جدید', 'ps': 'نوی ازموینه جوړول',
    },
    'build_quiz_subtitle': {
        'en': 'Build your quiz by adding details and questions below.', 'fa': 'آزمون خود را با افزودن جزئیات و سوالات بسازید.', 'ps': 'خپله ازموینه د معلوماتو او پوښتنو په زیاتولو جوړه کړئ.',
    },
    'draft_not_published': {
        'en': 'Draft — not published', 'fa': 'پیش‌نویس — منتشر نشده', 'ps': 'مسوده — نه ده خپره شوې',
    },
    'quiz_details': {
        'en': 'Quiz Details', 'fa': 'جزئیات آزمون', 'ps': 'د ازموینې جزئیات',
    },
    'set_quiz_rules': {
        'en': 'Set the title, subject, and rules for this quiz', 'fa': 'عنوان، موضوع و قوانین این آزمون را تنظیم کنید', 'ps': 'د دې ازموینې نوم، موضوع او قواعد وټاکئ',
    },
    'quiz_title_label': {
        'en': 'Quiz title', 'fa': 'عنوان آزمون', 'ps': 'د ازموینې نوم',
    },
    'subject': {
        'en': 'Subject', 'fa': 'موضوع', 'ps': 'موضوع',
    },
    'biology': {
        'en': 'Biology', 'fa': 'زیست‌شناسی', 'ps': 'بیولوژي',
    },
    'chemistry': {
        'en': 'Chemistry', 'fa': 'شیمی', 'ps': 'کیمیا',
    },
    'physics': {
        'en': 'Physics', 'fa': 'فیزیک', 'ps': 'فزیک',
    },
    'mathematics': {
        'en': 'Mathematics', 'fa': 'ریاضی', 'ps': 'ریاضي',
    },
    'history_subject': {
        'en': 'History', 'fa': 'تاریخ', 'ps': 'تاریخ',
    },
    'chapter_unit': {
        'en': 'Chapter / Unit', 'fa': 'فصل / واحد', 'ps': 'فصل / برخه',
    },
    'difficulty': {
        'en': 'Difficulty', 'fa': 'سختی', 'ps': 'ستونزوالی',
    },
    'easy': {
        'en': 'Easy', 'fa': 'آسان', 'ps': 'اسانه',
    },
    'medium': {
        'en': 'Medium', 'fa': 'متوسط', 'ps': 'منځنۍ',
    },
    'hard': {
        'en': 'Hard', 'fa': 'سخت', 'ps': 'سخت',
    },
    'duration_minutes': {
        'en': 'Duration (minutes)', 'fa': 'مدت (دقیقه)', 'ps': 'موده (دقیقې)',
    },
    'passing_score': {
        'en': 'Passing score (%)', 'fa': 'نمره قبولی (%)', 'ps': 'د بریالیتوب نمره (%)',
    },
    'attempts_allowed': {
        'en': 'Attempts allowed', 'fa': 'تعداد تلاش مجاز', 'ps': 'اجازه شوې هڅې',
    },
    'unlimited': {
        'en': 'Unlimited', 'fa': 'نامحدود', 'ps': 'بې حده',
    },
    'multiple_choice': {
        'en': 'Multiple choice', 'fa': 'چند گزینه‌ای', 'ps': 'څو انتخابي',
    },
    'question_text': {
        'en': 'Question text', 'fa': 'متن سوال', 'ps': 'د پوښتنې متن',
    },
    'answer_options': {
        'en': 'Answer options', 'fa': 'گزینه‌های پاسخ', 'ps': 'د ځواب انتخابونه',
    },
    'select_correct_answer': {
        'en': 'Select the correct answer', 'fa': 'پاسخ صحیح را انتخاب کنید', 'ps': 'سم ځواب وټاکئ',
    },
    'add_answer_option': {
        'en': 'Add answer option', 'fa': 'افزودن گزینه پاسخ', 'ps': 'د ځواب انتخاب زیاتول',
    },
    'single_choice': {
        'en': 'Single choice', 'fa': 'تک گزینه‌ای', 'ps': 'یو انتخاب',
    },
    'explanation': {
        'en': 'Explanation', 'fa': 'توضیحی', 'ps': 'توضیحي',
    },
    'free_text_answer': {
        'en': 'Student will write a free-text answer', 'fa': 'شاگرد پاسخ متنی می‌نویسد', 'ps': 'زده کوونکی خپل ځواب به لیکنه ولیکي',
    },
    'students_type_response': {
        'en': 'Students type their response in a text area. You grade it later.', 'fa': 'شاگردان پاسخ خود را در کادر متنی می‌نویسند. شما بعداً نمره می‌دهید.', 'ps': 'زده کوونکي ځواب په متن کې لیکنه لیکي. تاسو وروسته نمره ورکوئ.',
    },
    'use_open_questions': {
        'en': "Use this type for open-ended questions, essays, or short answers that can't be auto-graded.", 'fa': 'این نوع را برای سوالات باز، انشا یا پاسخ‌های کوتاهی که نمره خودکار ندارند استفاده کنید.', 'ps': 'دا ډول د خلاصو پوښتنو، مقالیو یا لنډو ځوابونو لپاره وکاروئ چې اتومات نمره نه شي.',
    },
    'manual_grading': {
        'en': 'Manual grading', 'fa': 'نمره‌دهی دستی', 'ps': 'لاسي نمره ورکول',
    },
    'no_questions_yet': {
        'en': 'No questions yet', 'fa': 'هنوز سوالی نیست', 'ps': 'لا تراوسه پوښتنه نشته',
    },
    'click_add_question': {
        'en': 'Click "Add a new question" below to get started.', 'fa': 'برای شروع روی «افزودن سوال جدید» کلیک کنید.', 'ps': 'د پیل لپاره لاندې «نوې پوښتنه زیاتول» کلیک کړئ.',
    },
    'add_new_question': {
        'en': 'Add a new question', 'fa': 'افزودن سوال جدید', 'ps': 'نوې پوښتنه زیاتول',
    },
    'choose_question_type': {
        'en': 'Choose question type', 'fa': 'نوع سوال را انتخاب کنید', 'ps': 'د پوښتنې ډول وټاکئ',
    },
    'multiple_choice_cap': {
        'en': 'Multiple Choice', 'fa': 'چند گزینه‌ای', 'ps': 'څو انتخابي',
    },
    'four_options_hint': {
        'en': '4 answer options with one correct answer.', 'fa': '۴ گزینه با یک پاسخ صحیح.', 'ps': '۴ د ځواب انتخابونه چې یو سم وي.',
    },
    'open_ended_hint': {
        'en': 'Open-ended text answer, graded manually.', 'fa': 'پاسخ متنی باز، با نمره‌دهی دستی.', 'ps': 'خلاص لیکني ځواب، لاسي نمره ورکول.',
    },
    'quiz_summary': {
        'en': 'Quiz Summary', 'fa': 'خلاصه آزمون', 'ps': 'د ازموینې لنډیز',
    },
    'total_points': {
        'en': 'Total points', 'fa': 'مجموع امتیاز', 'ps': 'ټول ټکي',
    },
    'question_types': {
        'en': 'Question types', 'fa': 'انواع سوالات', 'ps': 'د پوښتنو ډولونه',
    },
    'settings': {
        'en': 'Settings', 'fa': 'تنظیمات', 'ps': 'سمټونې',
    },
    'shuffle_questions': {
        'en': 'Shuffle questions', 'fa': 'بُر زدن سوالات', 'ps': 'پوښتنې ګډول',
    },
    'randomize_order': {
        'en': 'Randomize order', 'fa': 'ترتیب تصادفی', 'ps': 'تصادفي ترتیب',
    },
    'shuffle_answers': {
        'en': 'Shuffle answers', 'fa': 'بُر زدن گزینه‌ها', 'ps': 'ځوابونه ګډول',
    },
    'randomize_options': {
        'en': 'Randomize options', 'fa': 'گزینه‌های تصادفی', 'ps': 'تصادفي انتخابونه',
    },
    'show_answers': {
        'en': 'Show answers', 'fa': 'نمایش پاسخ‌ها', 'ps': 'ځوابونه ښودل',
    },
    'reveal_after_submit': {
        'en': 'Reveal after submit', 'fa': 'نمایش بعد از ارسال', 'ps': 'له سپارلو وروسته ښودل',
    },
    'time_limit': {
        'en': 'Time limit', 'fa': 'محدودیت زمان', 'ps': 'د وخت محدودیت',
    },
    'enforce_duration': {
        'en': 'Enforce duration', 'fa': 'اعمال مدت', 'ps': 'د مودې پلي کول',
    },
    'save_quiz': {
        'en': 'Save Quiz', 'fa': 'ذخیره آزمون', 'ps': 'ازموینه خوندي کول',
    },
    'preview_quiz': {
        'en': 'Preview Quiz', 'fa': 'پیش‌نمایش آزمون', 'ps': 'د ازموینې مخکتنه',
    },

    # ---- take_quiz.html ----
    'exit': {
        'en': 'Exit', 'fa': 'خروج', 'ps': 'وتل',
    },
    'to_pass': {
        'en': 'To pass', 'fa': 'برای قبولی', 'ps': 'د بریالیتوب لپاره',
    },
    'progress': {
        'en': 'Progress', 'fa': 'پیشرفت', 'ps': 'پرمختګ',
    },
    'answered_of': {
        'en': 'answered', 'fa': 'پاسخ داده شده', 'ps': 'ځواب ورکړل شوی',
    },
    'loading_question': {
        'en': 'Loading question...', 'fa': 'در حال بارگذاری سوال...', 'ps': 'د پوښتنې رالوډول...',
    },
    'previous': {
        'en': 'Previous', 'fa': 'قبلی', 'ps': 'پخوانی',
    },
    'next': {
        'en': 'Next', 'fa': 'بعدی', 'ps': 'بل',
    },
    'submit_quiz': {
        'en': 'Submit Quiz', 'fa': 'ارسال آزمون', 'ps': 'ازموینه سپارل',
    },
    'question_map': {
        'en': 'Question Map', 'fa': 'نقشه سوالات', 'ps': 'د پوښتنو نقشه',
    },
    'answered_label': {
        'en': 'Answered', 'fa': 'پاسخ داده شده', 'ps': 'ځواب ورکړل شوی',
    },
    'current_label': {
        'en': 'Current', 'fa': 'فعلی', 'ps': 'اوسنی',
    },
    'not_answered': {
        'en': 'Not answered', 'fa': 'پاسخ داده نشده', 'ps': 'ځواب نه دی ورکړل شوی',
    },
    'your_answer': {
        'en': 'Your answer', 'fa': 'پاسخ شما', 'ps': 'ستاسو ځواب',
    },
    'graded_manually_hint': {
        'en': 'This question will be graded manually by your teacher.', 'fa': 'این سوال به‌صورت دستی توسط مدرس نمره‌گذاری می‌شود.', 'ps': 'دا پوښتنه ستاسو ښوونکي لاسي نمره ورکوي.',
    },
    'submitting': {
        'en': 'Submitting...', 'fa': 'در حال ارسال...', 'ps': 'سپارل کیږي...',
    },

    # ---- quiz_result.html ----
    'passed_verdict': {
        'en': 'PASSED', 'fa': 'قبول شدید', 'ps': 'بریالی شول',
    },
    'not_passed_verdict': {
        'en': 'NOT PASSED', 'fa': 'رد شدید', 'ps': 'ناکام شوئ',
    },
    'awaiting_grading': {
        'en': 'AWAITING GRADING', 'fa': 'در انتظار نمره‌دهی', 'ps': 'د نمرې په تمه',
    },
    'your_answer_colon': {
        'en': 'Your answer:', 'fa': 'پاسخ شما:', 'ps': 'ستاسو ځواب:',
    },
    'correct_label': {
        'en': 'Correct:', 'fa': 'صحیح:', 'ps': 'سم:',
    },
    'teacher_feedback': {
        'en': 'Teacher feedback', 'fa': 'بازخورد مدرس', 'ps': 'د ښوونکي نظر',
    },

    # ---- quiz_submission.html ----
    'submissions_title': {
        'en': 'Submissions', 'fa': 'ارسالی‌ها', 'ps': 'سپارنې',
    },
    'graded_label': {
        'en': 'Graded', 'fa': 'نمره داده شده', 'ps': 'نمره شوې',
    },
    'open_btn': {
        'en': 'Open', 'fa': 'باز کردن', 'ps': 'خلاصول',
    },
    'no_submissions_yet': {
        'en': 'No submissions yet.', 'fa': 'هنوز ارسالی نیست.', 'ps': 'لا تراوسه سپارنه نشته.',
    },

    # ---- attempt_details.html ----
    'percentage': {
        'en': 'Percentage', 'fa': 'درصد', 'ps': 'سلنه',
    },
    'wrong': {
        'en': 'Wrong', 'fa': 'غلط', 'ps': 'غلط',
    },
    'needs_grading': {
        'en': 'Needs grading', 'fa': 'نیاز به نمره‌دهی', 'ps': 'نمرې ته اړتیا لري',
    },
    'student_picked': {
        'en': 'Student picked:', 'fa': 'انتخاب شاگرد:', 'ps': 'زده کوونکي ټاکل:',
    },
    'no_answer_selected': {
        'en': 'No answer selected.', 'fa': 'گزینه‌ای انتخاب نشده.', 'ps': 'هیڅ ځواب نه دی ټاکل شوی.',
    },
    'correct_answer_label': {
        'en': 'Correct answer:', 'fa': 'پاسخ صحیح:', 'ps': 'سم ځواب:',
    },
    'student_left_blank': {
        'en': 'Student left this blank.', 'fa': 'شاگرد این را خالی گذاشته است.', 'ps': 'زده کوونکي دا تش پرېښودلی.',
    },
    'points_range': {
        'en': 'Points', 'fa': 'امتیاز', 'ps': 'ټکي',
    },
    'feedback_optional': {
        'en': 'Feedback (optional)', 'fa': 'بازخورد (اختیاری)', 'ps': 'نظر (اختیاري)',
    },
    'total_score': {
        'en': 'Total score', 'fa': 'نمره کل', 'ps': 'ټولې نمرې',
    },
    'save_grades': {
        'en': 'Save Grades', 'fa': 'ذخیره نمرات', 'ps': 'نمرې خوندي کول',
    },

    # ---- priview.html ----
    'interactive_learning': {
        'en': 'Interactive Learning', 'fa': 'یادگیری تعاملی', 'ps': 'تعاملي زده کړه',
    },
    'loading_course': {
        'en': 'Loading course...', 'fa': 'در حال بارگذاری دوره...', 'ps': 'د کورس رالوډول...',
    },
    'category_label': {
        'en': 'Category', 'fa': 'دسته‌بندی', 'ps': 'کټګوري',
    },
    'views_label': {
        'en': 'views', 'fa': 'بازدید', 'ps': 'کتنې',
    },
    'description_placeholder': {
        'en': 'Course description will appear here.', 'fa': 'توضیحات دوره اینجا نمایش داده می‌شود.', 'ps': 'د کورس توضیحات دلته ښکاري.',
    },
    'senior_instructor': {
        'en': 'Senior Instructor', 'fa': 'مدرس ارشد', 'ps': 'لوړ ښوونکی',
    },
    'share_course': {
        'en': 'Share Course', 'fa': 'اشتراک دوره', 'ps': 'کورس شریکول',
    },
    'link_copied': {
        'en': '✨ Link copied!', 'fa': '✨ لینک کپی شد!', 'ps': '✨ لینک کاپي شو!',
    },

    # ---- forgot_password.html ----
    'reset_password_title': {
        'en': 'Reset your password', 'fa': 'بازنشانی رمز عبور', 'ps': 'پټ نوم بیا ټاکل',
    },
    'reset_step_email': {
        'en': 'Email', 'fa': 'ایمیل', 'ps': 'بریښنالیک',
    },
    'reset_step_verify': {
        'en': 'Verify', 'fa': 'تأیید', 'ps': 'تایید',
    },
    'reset_step_new_password': {
        'en': 'New password', 'fa': 'رمز عبور جدید', 'ps': 'نوی پټ نوم',
    },
    'account_email': {
        'en': 'Account email', 'fa': 'ایمیل حساب', 'ps': 'د حساب بریښنالیک',
    },
    'send_verification_code': {
        'en': 'Send verification code', 'fa': 'ارسال کد تأیید', 'ps': 'د تصدیق کوډ لېږل',
    },
    'six_digit_code': {
        'en': '6-digit verification code', 'fa': 'کد تأیید ۶ رقمی', 'ps': '۶ ځنګه تصدیق کوډ',
    },
    'code_expires_in': {
        'en': 'Code expires in', 'fa': 'کد منقضی می‌شود در', 'ps': 'کوډ پای مومي په',
    },
    'check_spam_folder': {
        'en': 'Check your spam folder if it has not arrived.', 'fa': 'اگر نرسید، پوشه هرزنامه را بررسی کنید.', 'ps': 'که نه رارسید شوی، سپیم فولډر وګورئ.',
    },
    'verify_code': {
        'en': 'Verify code', 'fa': 'تأیید کد', 'ps': 'کوډ تاییدول',
    },
    'code_confirmed_for': {
        'en': 'Code confirmed for', 'fa': 'کد برای این حساب تأیید شد:', 'ps': 'کوډ تایید شو لپاره',
    },
    'confirm_new_password': {
        'en': 'Confirm new password', 'fa': 'تکرار رمز عبور جدید', 'ps': 'نوی پټ نوم تاییدول',
    },
    'set_new_password': {
        'en': 'Set new password', 'fa': 'تنظیم رمز عبور جدید', 'ps': 'نوی پټ نوم کېښودل',
    },
    'password_hint_8': {
        'en': 'At least 8 characters, not a common password.', 'fa': 'حداقل ۸ کاراکتر، رمز معمولی نباشد.', 'ps': 'لږ تر لږه ۸ توري، عادي پټ نوم نه وي.',
    },
    'send_new_code': {
        'en': 'Send a new code', 'fa': 'ارسال کد جدید', 'ps': 'نوی کوډ لېږل',
    },
    'resend_code_in': {
        'en': 'Resend code in', 'fa': 'ارسال مجدد کد در', 'ps': 'بیا لېږل کوډ په',
    },

    # ---- teacher_add.html ----
    'create_account': {
        'en': 'Create Account', 'fa': 'ایجاد حساب', 'ps': 'حساب جوړول',
    },
    'welcome_bang': {
        'en': 'Welcome!', 'fa': 'خوش آمدید!', 'ps': 'ښه راغلاست!',
    },
    'join_thousands': {
        'en': 'Join thousands of learners building their future with us.', 'fa': 'به هزاران یادگیرنده بپیوندید که آینده خود را با ما می‌سازند.', 'ps': 'د زرګونه زده کوونکو سره یوځای شئ چې راتلونکي جوړوي.',
    },
    'fill_details': {
        'en': 'Please fill in your details', 'fa': 'لطفاً اطلاعات خود را وارد کنید', 'ps': 'لطف ا کره معلومات داخل کړئ',
    },
    'first_name': {
        'en': 'First Name', 'fa': 'نام', 'ps': 'لومړی نوم',
    },
    'last_name': {
        'en': 'Last Name', 'fa': 'نام خانوادگی', 'ps': 'تخلص',
    },
    'email_address': {
        'en': 'Email Address', 'fa': 'آدرس ایمیل', 'ps': 'برېښنالیک پته',
    },
    'confirm_password': {
        'en': 'Confirm Password', 'fa': 'تکرار رمز عبور', 'ps': 'پټ نوم تاییدول',
    },
    'create_my_account': {
        'en': 'Create My Account', 'fa': 'ساخت حساب من', 'ps': 'زما حساب جوړول',
    },
    'already_have_account': {
        'en': 'Already have an account?', 'fa': 'قبلاً حساب دارید؟', 'ps': 'لا دمخه حساب لرئ؟',
    },

    # ---- ai_assistant.html ----
    'ai_subtitle': {
        'en': 'Ask anything about your courses, lessons or study plan.', 'fa': 'هر سؤالی درباره دوره‌ها، درس‌ها یا برنامه مطالعه بپرسید.', 'ps': 'د کورسونو، درسونو یا د مطالعې پلان په اړه هر څه پوښتئ.',
    },
    'new_chat_word': {
        'en': 'New chat', 'fa': 'گفتگوی جدید', 'ps': 'نوې خبرې',
    },
    'clear_chat': {
        'en': 'Clear chat', 'fa': 'پاک کردن گفتگو', 'ps': 'خبرې پاکول',
    },
    'about_course': {
        'en': 'About course:', 'fa': 'درباره دوره:', 'ps': 'د کورس په اړه:',
    },
    'any_topic': {
        'en': 'Any topic', 'fa': 'هر موضوع', 'ps': 'هره موضوع',
    },
    'ask': {
        'en': 'Ask', 'fa': 'پرسیدن', 'ps': 'پوښتل',
    },
    'enter_to_send': {
        'en': 'Enter to send · Shift+Enter for a new line', 'fa': 'Enter برای ارسال · Shift+Enter خط جدید', 'ps': 'Enter لېږلو لپاره · Shift+Enter نوی کرښه',
    },

    # ---- admin_analytics.html ----
    'platform_analytics': {
        'en': 'Platform Analytics', 'fa': 'تحلیل پلتفرم', 'ps': 'د پلیټفارم شننې',
    },
    'total_users': {
        'en': 'Total Users', 'fa': 'مجموع کاربران', 'ps': 'ټول کاروونکي',
    },
    'published_label': {
        'en': 'Published', 'fa': 'منتشر شده', 'ps': 'خپاره شوی',
    },

    # ---- footer.html ----
    'footer_about': {
        'en': 'A modern and clean learning platform built with Django. Designed for performance, elegance, and an excellent user experience.',
        'fa': 'یک پلتفرم آموزشی مدرن و تمیز ساخته‌شده با جنگو. طراحی‌شده برای عملکرد، زیبایی و تجربه کاربری عالی.',
        'ps': 'یو عصري او پاک زده کړه پلیټفارم چې په جنجو جوړ شوی. د ښه فعالیت، ښکلا او غوره کارونې تجربې لپاره ډیزاین شوی.',
    },
    'quick_links': {
        'en': 'Quick Links', 'fa': 'لینک‌های سریع', 'ps': 'چټکې لینکونه',
    },
    'instructors': {
        'en': 'Instructors', 'fa': 'مدرسان', 'ps': 'ښوونکي',
    },
    'resources': {
        'en': 'Resources', 'fa': 'منابع', 'ps': 'سرچینې',
    },
    'documentation': {
        'en': 'Documentation', 'fa': 'مستندات', 'ps': 'اسناد',
    },
    'support_center': {
        'en': 'Support Center', 'fa': 'مرکز پشتیبانی', 'ps': 'د ملاتړ مرکز',
    },
    'privacy_policy': {
        'en': 'Privacy Policy', 'fa': 'سیاست حفظ حریم خصوصی', 'ps': 'د محرمیت پالیسي',
    },
    'terms_of_service': {
        'en': 'Terms of Service', 'fa': 'شرایط خدمات', 'ps': 'د خدمت شرایط',
    },
    'faqs': {
        'en': 'FAQs', 'fa': 'سوالات متداول', 'ps': 'عامه پوښتنې',
    },
    'contact_us': {
        'en': 'Contact Us', 'fa': 'تماس با ما', 'ps': 'زموږ سره اړیکه',
    },
    'phone': {
        'en': 'Phone', 'fa': 'تلفن', 'ps': 'تلیفون',
    },

    'export_csv': {
        'en': 'Export CSV', 'fa': 'خروجی CSV', 'ps': 'CSV صادرول',
    },
    'pass_rate': {
        'en': 'Pass rate', 'fa': 'نرخ قبولی', 'ps': 'د بریالیتوب کچه',
    },
    'quiz_performance': {
        'en': 'Quiz performance', 'fa': 'عملکرد آزمون‌ها', 'ps': 'د ازموینو فعالیت',
    },
    'my_courses_label': {
        'en': 'My courses', 'fa': 'دوره‌های من', 'ps': 'زما کورسونه',
    },
    'students_reached': {
        'en': 'Students Reached', 'fa': 'شاگردان رسیده', 'ps': 'رسېدلي زده کوونکي',
    },
    'quiz_attempts_label': {
        'en': 'Quiz Attempts', 'fa': 'تلاش‌های آزمون', 'ps': 'د ازموینې هڅې',
    },
    'daily_activity': {
        'en': 'Daily activity — last 14 days', 'fa': 'فعالیت روزانه — ۱۴ روز گذشته', 'ps': 'ورځنی فعالیت — تېرې ۱۴ ورځې',
    },
    'learning_outcomes': {
        'en': 'Learning outcomes', 'fa': 'نتایج یادگیری', 'ps': 'د زده کړې پایلې',
    },
    'avg_score': {
        'en': 'Avg score', 'fa': 'میانگین نمره', 'ps': 'منځنۍ نمره',
    },
    'avg_word': {
        'en': 'Avg %', 'fa': 'میانگین %', 'ps': 'منځنی %',
    },
    'courses_by_category': {
        'en': 'Courses by category', 'fa': 'دوره‌ها بر اساس دسته', 'ps': 'کورسونه پر کټګوري',
    },
    'courses_by_level': {
        'en': 'Courses by level', 'fa': 'دوره‌ها بر اساس سطح', 'ps': 'کورسونه پر کچه',
    },
    'recent_enrollments': {
        'en': 'Recent enrollments', 'fa': 'ثبت‌نام‌های اخیر', 'ps': 'وروستې نوم لیکنې',
    },
    'recent_comments': {
        'en': 'Recent comments', 'fa': 'نظرات اخیر', 'ps': 'وروستې تبصرې',
    },
    'top_courses_engagement': {
        'en': 'Top courses by engagement', 'fa': 'دوره‌های برتر بر اساس تعامل', 'ps': 'غوره کورسونه پر ګډون',
    },
    'top_teachers': {
        'en': 'Top teachers', 'fa': 'اساتید برتر', 'ps': 'غوره ښوونکي',
    },
    'most_active_students': {
        'en': 'Most active students', 'fa': 'فعال‌ترین شاگردان', 'ps': 'تر ټولو فعال زده کوونکي',
    },
    'no_enrollments_yet': {
        'en': 'No enrollments yet.', 'fa': 'هنوز ثبت‌نامی نیست.', 'ps': 'لا تراوسه نوم لیکنه نشته.',
    },
    'no_quizzes_yet': {
        'en': 'No quizzes yet.', 'fa': 'هنوز آزمونی نیست.', 'ps': 'لا تراوسه ازموینه نشته.',
    },
    'my_data_analysis': {
        'en': 'My Data Analysis', 'fa': 'تحلیل داده من', 'ps': 'زما د معلوماتو شننه',
    },
    'download_csv': {
        'en': 'Download CSV', 'fa': 'دانلود CSV', 'ps': 'CSV ډاونلوډ',
    },

    'loading': {
        'en': 'Loading…',
        'fa': 'در حال بارگذاری…',
        'ps': 'پورته کېږي…',
    },
    'saving': {
        'en': 'Saving…',
        'fa': 'در حال ذخیره…',
        'ps': 'خوندي کېږي…',
    },
    'deleting': {
        'en': 'Deleting…',
        'fa': 'در حال حذف…',
        'ps': 'ړنګېږي…',
    },
    'mark_all_read': {
        'en': 'Mark all as read',
        'fa': 'همه خوانده شد',
        'ps': 'ټول لوستل شوي',
    },
    'mark_read': {
        'en': 'Mark as read',
        'fa': 'علامت خوانده\u200cشده',
        'ps': 'لوستل شوی وښیه',
    },
    'no_notifications': {
        'en': "You're all caught up — no notifications yet.",
        'fa': 'فعلاً اعلانی ندارید.',
        'ps': 'تر اوسه کومه خبرتیا نشته.',
    },
    'notifications_error': {
        'en': 'Could not load notifications. Please try again.',
        'fa': 'بارگذاری اعلان\u200cها ممکن نشد. دوباره تلاش کنید.',
        'ps': 'خبرتیاوې پورته نه شوې. بیا هڅه وکړئ.',
    },
    'unread': {
        'en': 'Unread',
        'fa': 'خوانده\u200cنشده',
        'ps': 'نالوستل شوې',
    },
    'edit_profile': {
        'en': 'Edit profile',
        'fa': 'ویرایش پروفایل',
        'ps': 'پروفایل سمول',
    },
    'profile_picture': {
        'en': 'Profile picture',
        'fa': 'عکس پروفایل',
        'ps': 'د پروفایل انځور',
    },
    'profile_picture_hint': {
        'en': 'JPG, PNG, GIF or WEBP, up to 5 MB. Leave empty to keep the current picture.',
        'fa': 'JPG، PNG، GIF یا WEBP تا ۵ مگابایت. برای حفظ عکس فعلی خالی بگذارید.',
        'ps': 'JPG، PNG، GIF یا WEBP تر ۵ MB پورې. د اوسني انځور ساتلو لپاره یې خالي پرېږدئ.',
    },
    'email_login_hint': {
        'en': 'You sign in with this email address.',
        'fa': 'با این ایمیل وارد حساب می\u200cشوید.',
        'ps': 'تاسو په دې برېښنالیک ننوځئ.',
    },
    'edit_video': {
        'en': 'Edit video',
        'fa': 'ویرایش ویدیو',
        'ps': 'ویډیو سمول',
    },
    'delete_video': {
        'en': 'Delete video',
        'fa': 'حذف ویدیو',
        'ps': 'ویډیو ړنګول',
    },
    'video_title': {
        'en': 'Video title',
        'fa': 'عنوان ویدیو',
        'ps': 'د ویډیو سرلیک',
    },
    'video_title_hint': {
        'en': 'Leave empty to show the file name.',
        'fa': 'برای نمایش نام فایل خالی بگذارید.',
        'ps': 'د فایل نوم ښودلو لپاره یې خالي پرېږدئ.',
    },
    'playlist_position': {
        'en': 'Position in playlist',
        'fa': 'جایگاه در فهرست پخش',
        'ps': 'په لړۍ کې ځای',
    },
    'replace_video': {
        'en': 'Replace video file (optional)',
        'fa': 'جایگزینی فایل ویدیو (اختیاری)',
        'ps': 'د ویډیو فایل بدلول (اختیاري)',
    },
    'delete_video_confirm': {
        'en': 'This permanently removes the video from this course playlist. Other courses are not affected.',
        'fa': 'این ویدیو برای همیشه از فهرست پخش این دوره حذف می\u200cشود. دوره\u200cهای دیگر تغییری نمی\u200cکنند.',
        'ps': 'دا ویډیو د تل لپاره د دې کورس له لړۍ څخه ړنګېږي. نور کورسونه نه اغېزمن کېږي.',
    },
    'delete_account_blocked': {
        'en': 'Account deletion is currently unavailable:',
        'fa': 'حذف حساب در حال حاضر ممکن نیست:',
        'ps': 'د حساب ړنګول اوس ممکن نه دي:',
    },
    'delete_account_password_label': {
        'en': 'Type your current password to confirm',
        'fa': 'برای تأیید، رمز فعلی خود را وارد کنید',
        'ps': 'د تایید لپاره خپل اوسنی پاسورډ ولیکئ',
    },
    'enter_your_password': {
        'en': 'Enter your current password',
        'fa': 'رمز عبور فعلی خود را وارد کنید',
        'ps': 'خپل اوسنی پاسورډ ولیکئ',
    },
    'permanently_delete': {
        'en': 'Permanently delete',
        'fa': 'حذف دائمی',
        'ps': 'د تل لپاره ړنګول',
    },
}


def lang_for(user, cookie_lang=None) -> str:
    """Resolve the display language. Logged-in users get their saved
    choice (User.language); anonymous visitors fall back to the
    LANG_COOKIE value they picked before signing in."""
    code = None
    if getattr(user, 'is_authenticated', False):
        code = getattr(user, 'language', None)
    if code not in LANGUAGES and cookie_lang in LANGUAGES:
        code = cookie_lang
    return code if code in LANGUAGES else 'en'


def t(lang, key):
    return T.get(key, {}).get(lang, T.get(key, {}).get('en', ''))


def strings_for(lang):
    return {key: val.get(lang, val['en']) for key, val in T.items()}


def site_context(user, cookie_lang=None) -> dict:
    """Everything templates need: strings, direction, and the picker list."""
    lang = lang_for(user, cookie_lang)
    return {
        't': strings_for(lang),
        'lang': lang,
        'lang_dir': 'rtl' if lang in RTL_LANGUAGES else 'ltr',
        'languages': [
            {'code': code, 'name': LANGUAGE_NAMES[code], 'active': code == lang}
            for code in LANGUAGES
        ],
    }


def site_context_processor(request):
    """Django context processor so every template gets {{ t.* }}, {{ lang }}
    and {{ lang_dir }} automatically."""
    return site_context(
        request.user,
        request.COOKIES.get(settings.SITE_LANG_COOKIE),
    )
