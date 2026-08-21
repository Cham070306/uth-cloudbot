"""Build consistent, actionable answers for the complete 150-item FAQ dataset."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FAQ_FILE = ROOT / "data" / "sample" / "faqs.json"

WORKFLOWS = {
    "academic": (
        "mở cổng sinh viên và đối chiếu chương trình đào tạo, điều kiện học phần cùng thông báo của học kỳ",
        "ghi lại mã học phần, lớp, học kỳ và chụp màn hình trạng thái thao tác",
        "gửi cố vấn học tập hoặc Phòng Đào tạo các thông tin trên nếu hệ thống không cho thực hiện",
        "Chỉ xem mốc thời gian và điều kiện trên thông báo chính thức đang áp dụng cho khóa của bạn.",
    ),
    "finance": (
        "mở mục Tài chính/Học phí trên cổng sinh viên và đối chiếu từng khoản phải thu",
        "chuẩn bị mã sinh viên, biên lai hoặc mã giao dịch, thời gian và số tiền đã thanh toán",
        "liên hệ bộ phận tài chính qua kênh chính thức nếu dữ liệu chưa khớp; lưu lại nội dung phản hồi",
        "Không chuyển tiền theo tài khoản hoặc đường dẫn do nguồn không chính thức cung cấp.",
    ),
    "exam": (
        "kiểm tra lịch thi, quy định học phần và thông báo của giảng viên trên các kênh chính thức",
        "đối chiếu mã học phần, ngày, ca, phòng thi và tình trạng đủ điều kiện dự thi",
        "báo ngay cho giảng viên hoặc Phòng Đào tạo khi có sai lệch, kèm ảnh chụp và thông tin môn học",
        "Lịch, phòng và thủ tục có thể thay đổi; hãy kiểm tra lại sát ngày thi.",
    ),
    "schedule": (
        "mở thời khóa biểu cá nhân và thông báo lớp học phần để kiểm tra ngày, ca và phòng học",
        "đối chiếu mã lớp, tuần học và ghi lại thay đổi hoặc ảnh chụp liên quan",
        "xác nhận với giảng viên, lớp trưởng hoặc Phòng Đào tạo nếu hai nguồn hiển thị khác nhau",
        "Ưu tiên thông báo mới nhất có ngày ban hành và đúng lớp học phần của bạn.",
    ),
    "account": (
        "thử lại trên trang chính thức, kiểm tra kết nối, trình duyệt và thông tin đăng nhập",
        "dùng chức năng khôi phục tài khoản; không chia sẻ mật khẩu, OTP hoặc mã xác minh cho người khác",
        "liên hệ bộ phận hỗ trợ kèm mã sinh viên, thời điểm lỗi và ảnh chụp đã che dữ liệu nhạy cảm",
        "Không gửi mật khẩu, OTP hay API key qua email, tin nhắn hoặc biểu mẫu không xác thực.",
    ),
    "library": (
        "tra cứu trên cổng thư viện bằng tên tài liệu, tác giả, chủ đề hoặc mã tài liệu",
        "kiểm tra tình trạng còn sách, hạn mượn, quyền truy cập và hướng dẫn sử dụng tài nguyên",
        "liên hệ quầy thư viện bằng tài khoản sinh viên nếu cần gia hạn, xử lý mất sách hoặc hỗ trợ truy cập",
        "Tuân thủ hạn trả và điều kiện bản quyền; không chia sẻ tài khoản truy cập tài liệu điện tử.",
    ),
    "student": (
        "đọc thông báo của Phòng Công tác sinh viên, khoa hoặc đơn vị tổ chức để xác định điều kiện",
        "chuẩn bị mã sinh viên, biểu mẫu và minh chứng rõ thời gian, đơn vị tổ chức, nội dung tham gia",
        "nộp đúng kênh, lưu xác nhận và theo dõi trạng thái; phản hồi sớm nếu thông tin bị thiếu",
        "Kết quả chỉ được công nhận khi đáp ứng đúng tiêu chí và thời hạn của thông báo chính thức.",
    ),
    "internship": (
        "đọc kế hoạch thực tập của khoa để xác định điều kiện, mốc thời gian và biểu mẫu bắt buộc",
        "thống nhất nơi thực tập, giảng viên hướng dẫn, đề cương và đầu mối xác nhận tại doanh nghiệp",
        "lưu nhật ký, minh chứng, nhận xét và nộp báo cáo đúng định dạng qua kênh khoa công bố",
        "Mọi thay đổi về doanh nghiệp, đề tài hoặc người hướng dẫn cần được chấp thuận trước khi thực hiện.",
    ),
    "graduation": (
        "đối chiếu điều kiện trong kế hoạch của khoa và kiểm tra tiến độ học tập trên cổng sinh viên",
        "chuẩn bị đề cương, biểu mẫu, minh chứng, bản mềm/bản in theo đúng quy cách được công bố",
        "trao đổi với giảng viên hướng dẫn và theo dõi lịch nộp, phản biện, bảo vệ hoặc xét tốt nghiệp",
        "Không dùng lịch hoặc mẫu của khóa trước nếu chưa xác nhận vẫn còn hiệu lực.",
    ),
    "warning": (
        "xem kết quả học tập và thông báo cảnh báo trên cổng sinh viên để xác định nguyên nhân cụ thể",
        "lập danh sách môn nợ, học phần cần cải thiện và kế hoạch đăng ký phù hợp cho kỳ tiếp theo",
        "trao đổi sớm với cố vấn học tập hoặc Phòng Đào tạo và lưu lại phương án đã được hướng dẫn",
        "Mức cảnh báo và thời hạn xử lý phải đối chiếu theo quy chế áp dụng cho khóa của bạn.",
    ),
    "campus": (
        "ghi nhận vị trí, phòng, thời điểm và mô tả rõ vấn đề hoặc tài sản liên quan",
        "báo cho giảng viên, bảo vệ, quản lý phòng hoặc bộ phận cơ sở vật chất gần nhất",
        "cung cấp ảnh minh chứng khi an toàn và theo dõi mã/yêu cầu xử lý; không tự sửa thiết bị điện",
        "Với tài sản thất lạc, chỉ nhận lại qua đầu mối có xác minh và không công khai dữ liệu nhạy cảm.",
    ),
}

RANGES = [
    (1, 23, "academic"), (24, 24, "finance"), (25, 30, "student"),
    (31, 46, "academic"), (47, 59, "finance"), (60, 70, "exam"),
    (71, 82, "schedule"), (83, 89, "account"), (90, 97, "library"),
    (98, 110, "student"), (111, 119, "internship"), (120, 132, "graduation"),
    (133, 138, "warning"), (139, 142, "campus"),
]

CATEGORY_OVERRIDES = {
    3: "finance", 4: "account", 5: "account", 6: "campus", 7: "library",
    8: "library", 9: "student", 10: "student", 11: "student", 12: "student",
    13: "student", 14: "exam", 15: "exam", 16: "exam", 17: "graduation",
    18: "exam", 19: "student", 20: "student", 24: "finance", 25: "student",
    26: "student", 27: "student", 28: "internship", 29: "graduation", 30: "account",
}

INCIDENT_TERMS = (
    "mất", "quên", "khóa", "lỗi", "không nhận", "sai", "thiếu", "trùng",
    "vắng", "trễ", "hỏng", "thất lạc", "chưa cập nhật", "quá hạn",
)
LOOKUP_TERMS = (
    "tra cứu", "ở đâu", "khi nào", "thời gian", "lịch", "kết quả", "thông tin",
    "sơ đồ", "mức cảnh báo", "lịch sử",
)
CONDITION_TERMS = ("điều kiện", "cần gì", "dự thi", "tốt nghiệp", "làm đồ án")


def category_for(number):
    if number in CATEGORY_OVERRIDES:
        return CATEGORY_OVERRIDES[number]
    for start, end, name in RANGES:
        if start <= number <= end:
            return name
    raise ValueError(f"No category for FAQ {number}")

CUSTOM = {
    143: "Điện toán đám mây là mô hình cung cấp tài nguyên CNTT qua mạng theo nhu cầu.\n• Tài nguyên thường gồm máy chủ, lưu trữ, cơ sở dữ liệu, mạng và phần mềm.\n• Người dùng có thể mở rộng hoặc thu hẹp nhanh mà không phải tự sở hữu toàn bộ hạ tầng.\n• Chi phí thường dựa trên mức sử dụng.\nVí dụ: lưu tệp trên dịch vụ trực tuyến hoặc triển khai ứng dụng lên nền tảng cloud.",
    144: "IaaS, PaaS và SaaS khác nhau ở phần người dùng phải tự quản lý.\n• IaaS: thuê hạ tầng như máy ảo, mạng và ổ đĩa; bạn quản lý hệ điều hành và ứng dụng.\n• PaaS: nền tảng lo hạ tầng và môi trường chạy; bạn tập trung phát triển ứng dụng.\n• SaaS: dùng phần mềm hoàn chỉnh qua web hoặc ứng dụng.\nCó thể nhớ ngắn gọn: IaaS cho hạ tầng, PaaS cho môi trường phát triển, SaaS cho người dùng cuối.",
    145: "Điện toán đám mây giúp tổ chức triển khai dịch vụ nhanh và linh hoạt hơn.\n• Mở rộng tài nguyên theo nhu cầu thay vì mua sẵn toàn bộ thiết bị.\n• Truy cập dịch vụ từ nhiều nơi và hỗ trợ cộng tác.\n• Giảm công việc vận hành phần cứng tại chỗ.\n• Có công cụ sao lưu, giám sát và tự động hóa.\nLợi ích thực tế còn phụ thuộc kiến trúc, chi phí, bảo mật và năng lực quản trị.",
    146: "Cloud công cộng dùng hạ tầng do nhà cung cấp vận hành và chia sẻ theo cơ chế cô lập giữa nhiều khách hàng; cloud riêng dành cho một tổ chức.\n• Public cloud: triển khai nhanh, dễ mở rộng, ít đầu tư ban đầu.\n• Private cloud: kiểm soát và tùy biến cao hơn nhưng cần nguồn lực vận hành.\n• Hybrid cloud kết hợp hai mô hình.\nNên lựa chọn dựa trên dữ liệu, tuân thủ, chi phí, hiệu năng và đội ngũ kỹ thuật.",
    147: "UTH CloudBot hỗ trợ ba nhóm chức năng.\n• FAQ: trả lời các câu hỏi thủ tục từ bộ dữ liệu mẫu.\n• Trợ lý cá nhân: hiển thị lịch học, bài tập, kỳ thi và thông báo demo sau khi đăng nhập.\n• Gemini AI: giải thích kiến thức mở khi FAQ không phù hợp.\nMỗi câu trả lời đều có nhãn nguồn để người dùng phân biệt; dữ liệu demo không thay thế thông báo chính thức của UTH.",
    148: "Để CloudBot hiểu đúng, hãy nêu một nhu cầu trong mỗi câu và thêm ngữ cảnh cần thiết.\n• Tốt: “Tuần này tôi học những môn gì?”\n• Tốt: “Tra cứu học phí như thế nào?”\n• Tốt: “Giải thích IaaS cho người mới bắt đầu.”\nTránh câu quá ngắn như “lịch?” hoặc gộp nhiều yêu cầu. Không nhập mật khẩu, OTP, API key hay dữ liệu cá nhân nhạy cảm vào ô chat.",
    149: "Fallback xuất hiện khi câu hỏi chưa khớp FAQ, dữ liệu cá nhân hoặc Gemini đang không khả dụng.\n• Viết lại câu hỏi cụ thể hơn và chỉ hỏi một nội dung mỗi lần.\n• Kiểm tra trạng thái kết nối máy chủ.\n• Với câu hỏi cá nhân, hãy đăng nhập trước.\n• Với kiến thức mở, thử lại sau nếu Gemini đang lỗi.\nFallback là phản hồi an toàn, không phải thông tin chính thức để sử dụng ra quyết định.",
    150: "Câu trả lời từ Gemini được nhận biết bằng nhãn “Gemini AI” và ghi chú nội dung do AI tạo.\n• Nguồn FAQ có nhãn “FAQ”.\n• Lịch học, bài tập và dữ liệu cá nhân demo có nhãn “Dữ liệu demo”.\n• Khi hệ thống không xử lý được, nhãn là “Fallback”.\nNội dung Gemini có thể sai hoặc thiếu; hãy kiểm tra nguồn chuyên môn trước khi dùng cho học tập hay quyết định quan trọng.",
}


def workflow_for(number):
    return WORKFLOWS[category_for(number)]


def answer_kind(question):
    normalized = question.lower()
    if any(term in normalized for term in INCIDENT_TERMS):
        return "incident"
    if any(term in normalized for term in CONDITION_TERMS):
        return "condition"
    if any(term in normalized for term in LOOKUP_TERMS):
        return "lookup"
    return "procedure"


def subject_for(faq):
    question = faq["question"].strip().rstrip("?")
    patterns = (
        r"^Sinh viên cần làm gì về\s+",
        r"^Tra cứu thông tin\s+",
        r"^Hướng dẫn về\s+",
        r"^Tra cứu\s+",
        r"^Làm sao để\s+",
        r"^Xin\s+",
        r"^Điều kiện\s+",
    )
    for pattern in patterns:
        question = re.sub(pattern, "", question, flags=re.IGNORECASE)
    question = re.sub(
        r"\s+(như thế nào|thế nào|ra sao|ở đâu|khi nào|là gì|cần gì)$",
        "",
        question,
        flags=re.IGNORECASE,
    )
    return question.strip().lower()


def upper_first(value):
    return value[:1].upper() + value[1:]


def build_answer(number, faq):
    if number in CUSTOM:
        return CUSTOM[number]
    subject = subject_for(faq)
    step1, step2, step3, note = workflow_for(number)
    kind = answer_kind(faq["question"])
    if kind == "incident":
        return (
            f"Khi gặp vấn đề về {subject}, bạn nên xử lý sớm và giữ lại thông tin của lần thao tác bị lỗi.\n\n"
            "Cách xử lý:\n"
            f"1. {upper_first(step1)}.\n"
            f"2. {upper_first(step2)}.\n"
            f"3. {upper_first(step3)}.\n\n"
            "Thông tin nên chuẩn bị:\n"
            "• Mã số sinh viên và học kỳ đang xử lý.\n"
            f"• Nội dung liên quan đến {subject}, thời điểm xảy ra và ảnh chụp minh chứng.\n\n"
            f"Lưu ý: {note}"
        )
    if kind == "condition":
        return (
            f"Điều kiện liên quan đến {subject} cần được đối chiếu theo quy định áp dụng cho khóa và học kỳ của bạn.\n\n"
            "Nội dung cần kiểm tra:\n"
            f"• {upper_first(step1)}.\n"
            f"• {upper_first(step2)}.\n"
            "Cách xác nhận:\n"
            f"1. Kiểm tra trạng thái {subject} trên cổng sinh viên.\n"
            f"2. Nếu thông tin chưa rõ, {step3}.\n\n"
            f"Lưu ý: {note}"
        )
    if kind == "lookup":
        return (
            f"Bạn có thể tra cứu {subject} từ cổng sinh viên hoặc kênh được đơn vị phụ trách công bố.\n\n"
            "Các bước tra cứu:\n"
            f"1. {upper_first(step1)}.\n"
            f"2. {upper_first(step2)}.\n"
            f"3. Đối chiếu mã sinh viên, học kỳ và trạng thái của {subject} trước khi sử dụng thông tin.\n\n"
            "Nếu chưa thấy dữ liệu:\n"
            f"• {upper_first(step3)}.\n"
            "• Gửi kèm ảnh màn hình và thời điểm tra cứu để được kiểm tra nhanh hơn.\n\n"
            f"Lưu ý: {note}"
        )
    return (
        f"Để thực hiện {subject}, bạn nên chuẩn bị thông tin trước và làm theo đúng kênh được trường công bố.\n\n"
        "Quy trình đề xuất:\n"
        f"1. {upper_first(step1)}.\n"
        f"2. {upper_first(step2)}.\n"
        f"3. {upper_first(step3)}.\n\n"
        "Sau khi hoàn tất:\n"
        f"• Kiểm tra lại trạng thái {subject} trên hệ thống.\n"
        "• Lưu thông báo, biên nhận hoặc ảnh xác nhận để đối chiếu khi cần.\n\n"
        f"Lưu ý: {note}"
    )


def main():
    payload = json.loads(FAQ_FILE.read_text(encoding="utf-8"))
    faqs = payload["faqs"]
    if len(faqs) != 150:
        raise ValueError(f"Expected 150 FAQs, found {len(faqs)}")
    for number, faq in enumerate(faqs, 1):
        faq["answer"] = build_answer(number, faq)
    FAQ_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
