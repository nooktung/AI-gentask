"""
Risks Knowledge Base - Lưu trữ rủi ro với mitigation và solution
Dựa trên kinh nghiệm thực tế từ các sự kiện
"""

from typing import Dict, List, Any, Optional


# Risks knowledge base với đầy đủ thông tin: category, owner, mitigation, solution
RISKS_KNOWLEDGE_BASE = {
    "Cơ sở vật chất": {
        "BTC": [
            {
                "id": "CSVC-001",
                "title": "Bị mất đồ trong/sau khi diễn ra sự kiện",
                "level": "high",
                "description": "Đồ đạc của BTC hoặc người tham gia bị mất trong quá trình sự kiện",
                "mitigation": [
                    "Book phòng để đồ của BTC",
                    "Gas lighting thành viên BTC tự bảo quản tư trang",
                    "Hạn chế mang laptop"
                ],
                "solution": [
                    "Ban tổ chức chịu trách nhiệm đền bù tổn thất"
                ]
            }
        ],
        "Takecare": [
            {
                "id": "CSVC-002",
                "title": "Gian hàng bị sập",
                "level": "critical",
                "description": "Gian hàng bị sập gây nguy hiểm cho người tham gia",
                "mitigation": [
                    "Kiểm tra kỹ lưỡng gian hàng trước khi sử dụng và đảm bảo chúng được lắp đặt đúng cách",
                    "Hạn chế trưng bày quá nhiều vật nặng trên gian hàng"
                ],
                "solution": [
                    "Yêu cầu người tham gia di chuyển khỏi khu vực gian hàng bị sập",
                    "Khẩn trương khắc phục sự cố và đảm bảo an toàn cho khu vực gian hàng trước khi cho phép người tham gia quay lại",
                    "Cung cấp biển báo cảnh báo nguy hiểm"
                ]
            },
            {
                "id": "CSVC-003",
                "title": "Sân khấu sập",
                "level": "critical",
                "description": "Sân khấu bị sập gây nguy hiểm nghiêm trọng",
                "mitigation": [
                    "Kiểm tra kỹ lưỡng sân khấu trước khi sử dụng và đảm bảo nó được lắp đặt đúng cách",
                    "Hạn chế số lượng người đứng trên sân khấu cùng một lúc"
                ],
                "solution": [
                    "Yêu cầu người tham gia di chuyển khỏi khu vực sân khấu có vấn đề",
                    "Khẩn trương khắc phục sự cố và đảm bảo an toàn cho sân khấu trước khi tiếp tục",
                    "Hủy hoặc điều chỉnh chương trình biểu diễn nếu cần thiết để đảm bảo an toàn cho tất cả mọi người",
                    "Cung cấp biển báo cảnh báo nguy hiểm"
                ]
            },
            {
                "id": "CSVC-004",
                "title": "Hệ thống điện gặp trục trặc (mất điện)",
                "level": "critical",
                "description": "Mất điện đột ngột ảnh hưởng toàn bộ sự kiện",
                "mitigation": [
                    "Chuẩn bị máy phát điện dự phòng, đảm bảo nguồn cung cấp điện ổn định",
                    "Chuẩn bị đèn pin"
                ],
                "solution": [
                    "Sử dụng máy phát điện dự phòng",
                    "Thông báo cho người tham gia về sự cố và sử dụng đèn pin hướng dẫn họ di chuyển an toàn"
                ]
            },
            {
                "id": "CSVC-005",
                "title": "Hệ thống âm thanh bị lỗi, mất tiếng",
                "level": "high",
                "description": "Hệ thống âm thanh gặp sự cố, không phát ra tiếng",
                "mitigation": [
                    "Kiểm tra thật kỹ và thường xuyên hệ thống âm thanh trước sự kiện",
                    "Chuẩn bị thiết bị dự phòng như loa mic"
                ],
                "solution": [
                    "Nhanh chóng xác định phần nào của hệ thống gặp sự cố",
                    "Sử dụng thiết bị dự phòng đã chuẩn bị từ trước"
                ]
            },
            {
                "id": "CSVC-006",
                "title": "Thiết bị ánh sáng gặp trục trặc",
                "level": "high",
                "description": "Hệ thống ánh sáng bị hỏng hoặc không hoạt động",
                "mitigation": [
                    "Kiểm tra kỹ lưỡng thiết bị ánh sáng trước khi sử dụng, đảm bảo chúng được lắp đặt đúng cách",
                    "Chuẩn bị sẵn sàng thiết bị dự phòng cho các chỗ dễ xảy ra trục trặc nhất",
                    "Chỉ định người quản lý thiết bị ánh sáng, đảm bảo chúng được sử dụng đúng cách"
                ],
                "solution": [
                    "Xác định phần nào của hệ thống gặp sự cố và khắc phục nhanh chóng",
                    "Sử dụng thiết bị ánh sáng dự phòng",
                    "Thông báo cho người tham gia sự kiện về sự cố và thời gian khắc phục dự kiến"
                ]
            },
            {
                "id": "CSVC-007",
                "title": "Đồ trang trí bị hỏng, mất",
                "level": "medium",
                "description": "Đồ trang trí bị hư hỏng hoặc mất trong quá trình setup",
                "mitigation": [
                    "Kiểm tra độ chắc chắn và ghi chép rõ ràng số lượng đồ trang trí"
                ],
                "solution": [
                    "Dỡ ngay lập tức các đồ trang trí bị hư hỏng hoặc có nguy cơ mất an toàn",
                    "Sửa chữa hoặc thay thế bằng đồ trang trí khác"
                ]
            },
            {
                "id": "CSVC-008",
                "title": "Thiếu dụng cụ ở sân khấu",
                "level": "medium",
                "description": "Thiếu dụng cụ cần thiết cho các tiết mục biểu diễn",
                "mitigation": [
                    "Chuẩn bị danh sách những dụng cụ có trên sân khấu và check số lượng kỹ lưỡng trước khi diễn ra sự kiện",
                    "Chuẩn bị sẵn sàng dụng cụ dự phòng cho các vật dụng quan trọng",
                    "Chỉ định người quản lý dụng cụ và đảm bảo các vật dụng được sử dụng đúng cách"
                ],
                "solution": [
                    "Điều chỉnh phần trình diễn để phù hợp với dụng cụ sẵn có",
                    "Sử dụng dụng cụ dự phòng đã chuẩn bị từ trước"
                ]
            },
            {
                "id": "CSVC-009",
                "title": "Thiếu dụng cụ ở gian hàng",
                "level": "medium",
                "description": "Thiếu dụng cụ cần thiết cho các gian hàng",
                "mitigation": [
                    "Chuẩn bị danh sách những dụng cụ có trong các gian hàng và check số lượng kỹ lưỡng trước khi diễn ra sự kiện"
                ],
                "solution": [
                    "Sử dụng dụng cụ thay thế từ các gian hàng khác hoặc từ ban tổ chức"
                ]
            }
        ],
        "Nhà ma": [
            {
                "id": "CSVC-010",
                "title": "Thiếu đồ/ hỏng đồ sau ca chơi",
                "level": "medium",
                "description": "Đồ dùng trong nhà ma bị mất hoặc hỏng sau mỗi ca chơi",
                "mitigation": [
                    "Takecare cần nhắc trước khi người chơi đi ra khỏi nhà ma: phải trả hết đồ trong nhà ma cho takecare checkout để kiểm lại đồ"
                ],
                "solution": [
                    "Luôn sẵn đồ backup từ trước"
                ]
            },
            {
                "id": "CSVC-011",
                "title": "Âm thanh, ánh sáng bị hỏng",
                "level": "high",
                "description": "Thiết bị âm thanh, ánh sáng trong nhà ma bị hỏng",
                "mitigation": [
                    "Bắt đầu và sau khi kết thúc mỗi ngày cần kiểm tra lại thiết bị"
                ],
                "solution": [
                    "Chuẩn bị sẵn 1 thiết bị để có thể thay thế"
                ]
            },
            {
                "id": "CSVC-012",
                "title": "Tường nhà ma bị rách",
                "level": "medium",
                "description": "Tường nhà ma bị rách do tác động",
                "mitigation": [
                    "Làm tường nhà ma bằng 2 lớp: vải + bạt"
                ],
                "solution": [
                    "Có sẵn vải để thay thế hoặc có thêm đồ để che đi chỗ rách"
                ]
            },
            {
                "id": "CSVC-013",
                "title": "Có ánh sáng từ bên ngoài chiếu vào",
                "level": "low",
                "description": "Ánh sáng bên ngoài làm giảm hiệu ứng nhà ma",
                "mitigation": [
                    "Check kỹ trước mỗi ngày trước khi mở nhà ma"
                ],
                "solution": [
                    "Lấy vải đen hoặc bạc bịt lại chỗ bị hở"
                ]
            }
        ],
        "Media": [
            {
                "id": "CSVC-014",
                "title": "Thiết bị hỏng hóc hoặc mất cắp",
                "level": "critical",
                "description": "Thiết bị quay phim, chụp ảnh bị hỏng hoặc bị mất cắp",
                "mitigation": [
                    "Sử dụng các thiết bị bảo vệ chuyên dụng như túi đựng chuy đeo cổ hoặc dây máy ảnh",
                    "Bảo quản thiết bị ở khu vực an toàn"
                ],
                "solution": [
                    "Thông báo lên toàn bộ sự kiện để tìm lại thiết bị"
                ]
            }
        ]
    },
    "MC/Khách mời": {
        "Takecare": [
            {
                "id": "MC-001",
                "title": "MC đến muộn",
                "level": "high",
                "description": "MC không đến đúng giờ, ảnh hưởng timeline sự kiện",
                "mitigation": [
                    "Gửi thông báo lịch trình rõ ràng cho MC và yêu cầu họ xác nhận tham dự",
                    "Có thể cân nhắc về việc chuẩn bị 1 MC dự phòng",
                    "Take Care MC liên hệ và gọi MC đến chuẩn bị trước giờ hoạt động sân khấu"
                ],
                "solution": [
                    "Bắt đầu sự kiện đúng giờ như kế hoạch",
                    "Để MC dự phòng dẫn sự kiện thay thế"
                ]
            },
            {
                "id": "MC-002",
                "title": "MC gặp chấn thương khi dẫn",
                "level": "critical",
                "description": "MC bị chấn thương trong quá trình dẫn chương trình",
                "mitigation": [
                    "Chuẩn bị sẵn sàng các biện pháp an toàn ở khu vực biểu diễn, chuẩn bị sẵn dụng cụ y tế để sơ cứu",
                    "Có thể cân nhắc về việc chuẩn bị 1 MC dự phòng"
                ],
                "solution": [
                    "Để MC dự phòng dẫn sự kiện thay thế",
                    "Đưa MC bị thương đến phòng y tế",
                    "Nếu bị thương nặng, liên hệ với cơ quan y tế"
                ]
            },
            {
                "id": "MC-003",
                "title": "MC quên script",
                "level": "medium",
                "description": "MC quên nội dung cần dẫn",
                "mitigation": [
                    "In nhiều bản script MC"
                ],
                "solution": [
                    "Đưa cho MC bản khác"
                ]
            },
            {
                "id": "MC-004",
                "title": "MC mắc lỗi",
                "level": "low",
                "description": "MC mắc lỗi khi dẫn chương trình",
                "mitigation": [
                    "Chuẩn bị kỹ lưỡng kịch bản sự kiện và tập luyện với MC",
                    "Hướng dẫn MC về phong cách dẫn sự kiện phù hợp với concept"
                ],
                "solution": [
                    "Linh hoạt xử lý tình huống khi MC mắc lỗi"
                ]
            },
            {
                "id": "MC-005",
                "title": "Khách mời đến muộn",
                "level": "high",
                "description": "Khách mời không đến đúng giờ",
                "mitigation": [
                    "Gửi thông báo lịch trình rõ ràng cho khách mời và yêu cầu họ xác nhận tham dự",
                    "Remind khách mời khi D-Day sắp tới"
                ],
                "solution": [
                    "Bắt đầu chương trình đúng giờ như kế hoạch",
                    "Nhờ MC kéo dài thời gian"
                ]
            },
            {
                "id": "MC-006",
                "title": "Khách mời yêu cầu, đòi hỏi quá cao những điều không có trong hợp đồng trong ngày D-day",
                "level": "high",
                "description": "Khách mời đưa ra yêu cầu vượt quá thỏa thuận",
                "mitigation": [
                    "Lựa chọn khách mời phù hợp với ngân sách và khả năng đáp ứng của ban tổ chức",
                    "Trao đổi rõ ràng với khách mời về các yêu cầu trước khi sự kiện diễn ra"
                ],
                "solution": [
                    "Giữ thái độ bình tĩnh, chuyên nghiệp khi đối mặt với yêu cầu của khách mời",
                    "Giải thích rõ ràng những hạn chế của ban tổ chức, tìm kiếm phương án giải quyết hợp lý cho cả hai bên",
                    "Nếu cần thiết, có thể cân nhắc việc thay thế khách mời"
                ]
            },
            {
                "id": "MC-007",
                "title": "Khách mời gặp chấn thương khi biểu diễn",
                "level": "critical",
                "description": "Khách mời bị chấn thương trong quá trình biểu diễn",
                "mitigation": [
                    "Yêu cầu khách mời đảm bảo họ có đủ điều kiện sức khỏe để tham gia biểu diễn",
                    "Chuẩn bị sẵn sàng các biện pháp an toàn ở khu vực biểu diễn, chuẩn bị sẵn dụng cụ y tế để sơ cứu"
                ],
                "solution": [
                    "Đưa khách mời bị thương đến phòng y tế",
                    "Nếu bị thương nặng, liên hệ với cơ quan y tế",
                    "Hủy hoặc tạm dừng tiết mục của khách mời"
                ]
            },
            {
                "id": "MC-008",
                "title": "Khách mời có các hành vi như: Gây rối, ngôn từ không phù hợp, hút chất cấm,...",
                "level": "critical",
                "description": "Khách mời có hành vi không phù hợp",
                "mitigation": [
                    "Trao đổi quy tắc ứng xử rõ ràng cho khách mời",
                    "Chuẩn bị sẵn sàng các biện pháp xử lý trong trường hợp khách mời có hành vi không phù hợp"
                ],
                "solution": [
                    "Nhắc nhở khách mời về quy tắc ứng xử",
                    "Áp dụng các biện pháp xử lý phù hợp như cảnh cáo, yêu cầu rời khỏi chương trình hoặc báo cáo cơ quan chức năng"
                ]
            }
        ]
    },
    "Truyền thông": {
        "Truyền thông": [
            {
                "id": "TT-001",
                "title": "Lượng tiếp cận tương tác thấp",
                "level": "medium",
                "description": "Bài đăng truyền thông không đạt được mục tiêu tương tác",
                "mitigation": [
                    "BTC seeding nhiệt tình",
                    "Viết những content thu hút người đọc",
                    "Hỗ trợ truyền thông"
                ],
                "solution": [
                    "Đẩy mạnh tương tác bằng cách share bài, tạo nên hiệu ứng truyền thông mạnh mẽ"
                ]
            }
        ]
    },
    "Người chơi": {
        "Takecare": [
            {
                "id": "NG-001",
                "title": "Take Care check sai kết quả của người chơi",
                "level": "medium",
                "description": "Nhân viên Takecare kiểm tra sai kết quả của người chơi",
                "mitigation": [
                    "Cung cấp cho Take Care hướng dẫn rõ ràng về cách thức check kết quả của người chơi",
                    "Cho phép người chơi kiểm tra lại kết quả nếu họ nghi ngờ có sai sót"
                ],
                "solution": [
                    "Sửa kết quả nếu có sai sót",
                    "Xin lỗi người chơi vì sự bất tiện mình gây ra"
                ]
            }
        ]
    },
    "Nhân sự": {
        "Hậu cần": [
            {
                "id": "NS-001",
                "title": "Thiếu nhân lực (nam - làm việc nặng)",
                "level": "high",
                "description": "Thiếu nhân lực nam để thực hiện các công việc nặng",
                "mitigation": [
                    "Trong lúc tuyển BTC, dự trù trước bao nhiêu nữ, nam cần thiết"
                ],
                "solution": [
                    "Nhờ các ban khác hỗ trợ",
                    "Sử dụng thành những món đồ làm sẵn với giá thành không chênh lệch quá mức cho phép"
                ]
            }
        ],
        "BTC": [
            {
                "id": "NS-002",
                "title": "Thành viên không nắm rõ thông tin deadline/cách thức làm việc",
                "level": "medium",
                "description": "Thành viên không hiểu rõ về deadline và quy trình làm việc",
                "mitigation": [
                    "Nhắc nhở các nhân sự trong ban, tuân thủ nội quy, bám sát vào tiến độ công việc"
                ],
                "solution": [
                    "Yêu cầu thành viên cf 100% tiến độ công việc cũng như luôn theo sát, giải đáp thắc mắc của thành viên"
                ]
            },
            {
                "id": "NS-003",
                "title": "Không thống nhất về cách làm việc giữa thành viên trong ban/với các ban trong BTC",
                "level": "high",
                "description": "Thiếu sự thống nhất trong cách làm việc",
                "mitigation": [
                    "Thống nhất cách làm việc của mọi người trong ban cũng như các ban khác trong BTC"
                ],
                "solution": [
                    "Trưởng ban nói chuyện với những nhân sự đang gặp vấn đề trong ban, giải quyết những khúc mắc của mọi người"
                ]
            },
            {
                "id": "NS-004",
                "title": "Thiếu người",
                "level": "high",
                "description": "Không đủ nhân sự để thực hiện công việc",
                "mitigation": [
                    "Lên danh sách, phân chia thành viên kỹ lưỡng cho từng mảng công việc",
                    "Lập kế hoạch chi tiết cho việc phân công công việc"
                ],
                "solution": [
                    "Phân chia người linh hoạt để đảm bảo đủ người cho các nơi quan trọng",
                    "Nhờ sự giúp đỡ từ các thành viên ban khác"
                ]
            },
            {
                "id": "NS-005",
                "title": "Thành viên không nghiêm túc",
                "level": "medium",
                "description": "Thành viên không có thái độ nghiêm túc trong công việc",
                "mitigation": [
                    "Lựa chọn thành viên có kinh nghiệm, tinh thần trách nhiệm cao",
                    "Tổ chức buổi training cho thành viên về nội dung chương trình, quy định và yêu cầu công việc",
                    "Trao đổi rõ ràng với thành viên về mong muốn và yêu cầu của ban tổ chức"
                ],
                "solution": [
                    "Nhắc nhở thành viên về trách nhiệm và yêu cầu công việc",
                    "Áp dụng các biện pháp kỷ luật nếu thành viên tiếp tục vi phạm",
                    "Nhờ sự giúp đỡ từ các thành viên ban khác"
                ]
            },
            {
                "id": "NS-006",
                "title": "Thành viên đến muộn",
                "level": "medium",
                "description": "Thành viên không đến đúng giờ",
                "mitigation": [
                    "Remind, nhắc nhở thành viên rõ ràng về lịch trình của sự kiện"
                ],
                "solution": [
                    "Bắt đầu chương trình đúng giờ như kế hoạch",
                    "Cập nhật về chương trình cho thành viên khi họ đến để họ theo kịp tiến độ sự kiện"
                ]
            },
            {
                "id": "NS-007",
                "title": "Thành viên báo vắng/nghỉ sát giờ tổ chức với lý do sức khoẻ, tai nạn,....",
                "level": "high",
                "description": "Thành viên báo vắng đột ngột trước giờ sự kiện",
                "mitigation": [
                    "Yêu cầu thành viên cung cấp thông tin về sức khỏe và đảm bảo họ có đủ điều kiện để tham gia sự kiện",
                    "Nếu thành viên cảm thấy sức khoẻ không ổn, không thể chạy sự kiện, báo ngay cho Lead/Sublead để xử lý kịp thời"
                ],
                "solution": [
                    "Nhờ sự giúp đỡ từ các thành viên ban khác trong trường hợp thành viên đó không đến kịp"
                ]
            },
            {
                "id": "NS-008",
                "title": "Mọi người chậm deadline",
                "level": "high",
                "description": "Nhiều thành viên không hoàn thành công việc đúng deadline",
                "mitigation": [
                    "Chủ động clear trước công việc, remind trước mỗi công việc quan trọng trên group"
                ],
                "solution": [
                    "Nhắc nhở và có hình phạt"
                ]
            },
            {
                "id": "NS-009",
                "title": "Thành viên làm mất đồ/ tiền của sự kiện và có ảnh hưởng đến quá trình diễn ra sự kiện",
                "level": "critical",
                "description": "Thành viên làm mất tài sản quan trọng của sự kiện",
                "mitigation": [
                    "Yêu cầu thành viên cất giữ đồ đạc cẩn thận và không mang theo những vật dụng không cần thiết",
                    "Kiểm tra danh sách đồ dùng và tiền bạc của sự kiện chi tiết",
                    "Giám sát hoạt động của thành viên trong suốt sự kiện",
                    "Tổ chức các buổi huấn luyện về cách xử lý tiền và vật phẩm quý giá một cách an toàn cho các thành viên trong nhóm thành viên"
                ],
                "solution": [
                    "Liên lạc với bảo vệ và cảnh sát",
                    "Cá nhân làm mất tự chịu trách nhiệm và bồi thường nếu không thể tìm thấy đồ/tiền bị mất"
                ]
            },
            {
                "id": "NS-010",
                "title": "Thành viên gặp tai nạn trong sự kiện",
                "level": "critical",
                "description": "Thành viên bị tai nạn trong quá trình làm việc",
                "mitigation": [
                    "Đảm bảo môi trường diễn ra sự kiện an toàn",
                    "Nhắc mọi người chú ý an toàn khi chạy sự kiện"
                ],
                "solution": [
                    "Cấp cứu y tế kịp thời cho thành viên gặp nạn"
                ]
            },
            {
                "id": "NS-011",
                "title": "Thành viên bị mệt giữa ca",
                "level": "medium",
                "description": "Thành viên bị mệt mỏi trong quá trình làm việc",
                "mitigation": [
                    "Luôn đảm bảo sức khỏe tốt nhất để có thể hoàn thành công việc được giao"
                ],
                "solution": [
                    "Cho ra nghỉ ngơi và thay thế thành viên khác làm thay"
                ]
            },
            {
                "id": "NS-012",
                "title": "Thành viên thiếu gắn kết, động lực làm việc",
                "level": "low",
                "description": "Thành viên không có động lực và gắn kết với công việc",
                "mitigation": [
                    "Khen thưởng và ghi nhận thành tích của mọi người",
                    "Lập ra nhiều kế hoạch bonding để mọi người hiểu rõ nhau hơn"
                ],
                "solution": [
                    "Trò chuyện, tâm sự với mọi người để hiểu rõ nguyên nhân thiếu động lực"
                ]
            },
            {
                "id": "NS-013",
                "title": "Thành viên xảy ra mâu thuẫn: Tranh cãi, xô xát",
                "level": "high",
                "description": "Có mâu thuẫn giữa các thành viên",
                "mitigation": [
                    "Phổ biến về quy định, nội quy, văn hoá làm việc, ứng xử khi tham gia sự kiện trước khi sự kiện diễn ra"
                ],
                "solution": [
                    "Can thiệp trực tiếp để hoà giải mâu thuẫn giữa các cá nhân",
                    "Ghi nhận thông tin sự việc để có biện pháp xử lý sau sự kiện"
                ]
            }
        ],
        "Nhà ma": [
            {
                "id": "NS-014",
                "title": "NPC xảy ra vấn đề",
                "level": "medium",
                "description": "NPC (Non-Player Character) trong nhà ma gặp vấn đề",
                "mitigation": [
                    "Training kỹ trước khi bắt tay vào làm",
                    "Có buổi nói chuyện sau mỗi ngày để tìm ra điểm chưa tốt và khắc phục vào hôm sau"
                ],
                "solution": [
                    "Thay NPC khác vào ca tiếp theo"
                ]
            }
        ],
        "Đối ngoại": [
            {
                "id": "NS-015",
                "title": "Không đạt đủ KPI",
                "level": "high",
                "description": "Ban đối ngoại không đạt được KPI về tài trợ",
                "mitigation": [
                    "Lên lộ trình đối ngoại rõ ràng, chạy đối ngoại sớm để chuẩn bị KPI đầy đủ"
                ],
                "solution": [
                    "Chuẩn bị sẵn các deal tài trợ khẩn cấp những contact NTT tiềm năng đã liên hệ trước"
                ]
            }
        ]
    },
    "Tuyến bài": {
        "Truyền thông": [
            {
                "id": "TB-001",
                "title": "Lên bài không đúng timeline",
                "level": "medium",
                "description": "Bài đăng truyền thông không được đăng đúng thời gian",
                "mitigation": [
                    "Trưởng ban giám sát, nhắc nhở nhân sự hoàn thành công việc đúng deadline"
                ],
                "solution": [
                    "Chỉnh sửa lên gấp tuyến bài trong thời gian còn tương tác"
                ]
            },
            {
                "id": "TB-002",
                "title": "Đưa thông tin sai lệch",
                "level": "high",
                "description": "Thông tin trong bài đăng không chính xác",
                "mitigation": [
                    "Kiểm duyệt nội dung trước khi up bài"
                ],
                "solution": [
                    "Sau khi thấy thông tin sai lệch, lập tức kiểm duyệt lại nội dung",
                    "Đàm phán, nói chuyện lại với bên đưa ra thông tin và trong trường hợp bắt buộc thì lập tức xoá bài và lên bài đính chính/xin lỗi",
                    "Yêu cầu BTC seeding, đẩy tương tác theo hướng tích cực"
                ]
            },
            {
                "id": "TB-003",
                "title": "Khủng hoảng truyền thông do có xích mích",
                "level": "critical",
                "description": "Xảy ra khủng hoảng truyền thông do mâu thuẫn",
                "mitigation": [
                    "Yêu cầu các thành viên không tham gia bất cứ vào tranh chấp nào"
                ],
                "solution": [
                    "Sau khi thấy thông tin sai lệch, lập tức kiểm duyệt lại nội dung",
                    "Đàm phán, nói chuyện lại với bên đưa ra thông tin và trong trường hợp bắt buộc thì lập tức xoá bài và lên bài đính chính/xin lỗi",
                    "Yêu cầu BTC seeding, đẩy tương tác theo hướng tích cực"
                ]
            }
        ]
    },
    "Người tham gia": {
        "Takecare": [
            {
                "id": "NTG-001",
                "title": "Làm loạn, phá sự kiện",
                "level": "high",
                "description": "Người tham gia có hành vi phá hoại sự kiện",
                "mitigation": [
                    "Training Take Care an ninh kĩ càng"
                ],
                "solution": [
                    "Nhắc nhở nhẹ nhàng, nếu họ không nghe sẽ yêu cầu rời khỏi sự kiện"
                ]
            },
            {
                "id": "NTG-002",
                "title": "Gặp chấn thương khi tham gia sự kiện",
                "level": "critical",
                "description": "Người tham gia bị chấn thương",
                "mitigation": [
                    "Nhắc nhở người tham gia cẩn thận khi vui chơi và tránh xa các nơi có thể dễ chấn thương (nhất là Takecare sân khấu)"
                ],
                "solution": [
                    "Đưa người bị thương vào phòng y tế"
                ]
            },
            {
                "id": "NTG-003",
                "title": "Số lượng người tham gia vượt quá dự kiến",
                "level": "high",
                "description": "Số lượng người tham gia nhiều hơn dự kiến",
                "mitigation": [
                    "Ước tính số lượng người tham gia dựa trên dữ liệu của các sự kiện diễn ra và các năm trước"
                ],
                "solution": [
                    "Chuẩn bị sẵn sàng phương án tiếp đón một số lượng người tham gia lớn hơn dự kiến như mở rộng khu vực tổ chức sự kiện, bố trí thêm các điểm check-in, khu vực vui chơi giải trí,...."
                ]
            },
            {
                "id": "NTG-004",
                "title": "Người tham gia không tuân thủ quy định sự kiện",
                "level": "medium",
                "description": "Người tham gia vi phạm quy định",
                "mitigation": [
                    "Cung cấp, phổ biến rõ ràng về quy định của sự kiện cho người tham gia qua page, mạng xã hội, tại bảng thông báo tại địa điểm tổ chức"
                ],
                "solution": [
                    "Nhắc nhở người tham gia tuân thủ quy định",
                    "Sử dụng lực lượng an ninh để đảm bảo trật tự và an toàn cho sự kiện",
                    "Nếu vẫn vi phạm, áp dụng biện pháp xử lý phù hợp với quy định"
                ]
            }
        ],
        "Nhà ma": [
            {
                "id": "NTG-005",
                "title": "Đội tham gia phải đợi quá lâu để đến lượt",
                "level": "medium",
                "description": "Người chơi phải chờ đợi quá lâu",
                "mitigation": [
                    "Nhắc nhở đội tham gia đến sớm để được chơi trước"
                ],
                "solution": [
                    "Nếu đợi quá lâu có thể nhắc đội chơi quay lại sau 30p nữa"
                ]
            },
            {
                "id": "NTG-006",
                "title": "Đội chơi đến nhầm ngày/ muốn đổi ngày",
                "level": "low",
                "description": "Người chơi đến sai ngày hoặc muốn đổi lịch",
                "mitigation": [
                    "Ghi rõ ngày mà đội chơi có thể chơi trên vé và nhắc nhở người chơi chú ý ngày chơi"
                ],
                "solution": [
                    "Có thể đổi lịch cho người chơi vào ngày hôm sau và sửa lại ngày trên vé"
                ]
            },
            {
                "id": "NTG-007",
                "title": "Có người tham gia bị ngất/thương",
                "level": "critical",
                "description": "Người chơi bị ngất hoặc thương trong nhà ma",
                "mitigation": [
                    "Nhắc người tham gia về các yếu tố jumpscare, không cho người có tiền sử bệnh tim vào"
                ],
                "solution": [
                    "Đưa người bị ngất đưa đến phòng y tế của trường"
                ]
            },
            {
                "id": "NTG-008",
                "title": "Hết thời gian nhưng đội chơi không chịu ra",
                "level": "medium",
                "description": "Đội chơi không chịu ra khi hết thời gian",
                "mitigation": [
                    "Thông báo thời gian chơi rõ ràng cho đội chơi từ trước"
                ],
                "solution": [
                    "Sẽ có takecare vào để mời đội chơi ra, trong trường hợp xấu nhất sẽ phải áp chế ra ngoài"
                ]
            },
            {
                "id": "NTG-009",
                "title": "Có những ca ít người tham gia",
                "level": "low",
                "description": "Số lượng người chơi ít hơn dự kiến",
                "mitigation": [
                    "Nếu là đội mua vé trong hôm DDay sẽ được giảm xuống còn 30k/người",
                    "Nếu là đội mua vé từ trước sẽ được tặng 1 cuốn sổ",
                    "Nhắc nhở người chơi đến sớm để nhận quà và không bị đợi lâu"
                ],
                "solution": [
                    "Đăng bài truyền thông và mời những người đi ở ngoài"
                ]
            }
        ]
    },
    "Thời tiết": {
        "BTC": [
            {
                "id": "TT-001",
                "title": "Thời tiết xấu",
                "level": "high",
                "description": "Thời tiết không thuận lợi cho sự kiện",
                "mitigation": [
                    "Cập nhật tình hình thời tiết liên tục trước 1 tuần diễn ra sự kiện để kịp chỉnh sửa, có phương án dự phòng cho những mục bị ảnh hưởng trực tiếp",
                    "Đảm bảo chuẩn bị các mái che, nhà bạt hay không gian để che nắng, che mưa có thể sử dụng tốt"
                ],
                "solution": [
                    "Nếu thời tiết quá xấu gây cản trở lớn đến kế hoạch tổ chức không thể tiếp tục -> Di chuyển sân khấu về sảnh Delta"
                ]
            }
        ]
    },
    "Thời gian": {
        "Nội dung": [
            {
                "id": "TG-001",
                "title": "Cháy timeline",
                "level": "high",
                "description": "Chương trình không theo đúng timeline",
                "mitigation": [
                    "Lên timeline có dự phòng thời gian phù hợp"
                ],
                "solution": [
                    "Quản trò/ MC đẩy nhanh hoặc làm chậm tiến độ của trò chơi để điều chỉnh thời gian phù hợp cho các tiết mục khác"
                ]
            }
        ],
        "Nhà ma": [
            {
                "id": "TG-002",
                "title": "Cháy timeline đội chơi",
                "level": "medium",
                "description": "Timeline của các đội chơi bị cháy",
                "mitigation": [
                    "Đẩy nhanh thời gian check lại đồ, thời gian delay giữa các đội tham gia, mở sớm hơn dự kiến 30p, bám sát vào agenda"
                ],
                "solution": [
                    "Xin lỗi đội tham gia và sắp lại lịch cho đội chơi vào ngày tiếp theo",
                    "Nếu đã là hôm cuối DDay thì sẽ cố mở thêm thời gian 1 chút để hoàn thành tất cả các đội chơi"
                ]
            }
        ],
        "Media": [
            {
                "id": "TG-003",
                "title": "Cháy timeline, không đổ ảnh kịp thời gian dự kiến",
                "level": "high",
                "description": "Media không kịp xử lý và đăng ảnh",
                "mitigation": [
                    "Chỉ định KPI cho từng nhân sự"
                ],
                "solution": [
                    "Thông báo với truyền thông lập tức, đưa ra các phương pháp và thời gian đổ ảnh sau đó để tiếp tục update các thông tin của sự kiện lên Fanpage"
                ]
            }
        ]
    },
    "Vé": {
        "Nhà ma": [
            {
                "id": "VE-001",
                "title": "Thừa vé sau hôm truyền thông off",
                "level": "low",
                "description": "Còn nhiều vé chưa bán được",
                "mitigation": [
                    "Tích cực truyền thông trên fanpage và bàn TT off"
                ],
                "solution": [
                    "Bán tiếp trong hôm DDay nhưng với giá gốc là 50k/vé"
                ]
            },
            {
                "id": "VE-002",
                "title": "Có sai sót thông tin giữa vé và trong sheet",
                "level": "medium",
                "description": "Thông tin trên vé không khớp với sheet",
                "mitigation": [
                    "Người làm sheet cần chú ý check lại những thông tin trước khi đội tham gia cầm vé đi"
                ],
                "solution": [
                    "Sửa lại thông tin khi thấy tình trạng sai sót và xin lỗi nếu sự sai sót có ảnh hưởng đến trải nghiệm của đội tham gia"
                ]
            }
        ]
    },
    "Ấn phẩm": {
        "Design": [
            {
                "id": "AP-001",
                "title": "Chưa nắm rõ được concept",
                "level": "medium",
                "description": "Designer không hiểu rõ concept của sự kiện",
                "mitigation": [
                    "Thống nhất rõ ràng các tông màu, các hình ảnh có liên quan, concept,..."
                ],
                "solution": [
                    "Sửa lại ấn phẩm ngay khi được nhận xét"
                ]
            },
            {
                "id": "AP-002",
                "title": "Ấn phẩm bị sai font, sai quy chuẩn về ảnh, sai tông màu, lỗi định dạng,...",
                "level": "high",
                "description": "Ấn phẩm không đúng yêu cầu kỹ thuật",
                "mitigation": [
                    "Thống nhất lại về các yêu cầu như font chữ, viền và màu,... trước khi design",
                    "Check từ sớm để tránh sát giờ lên bài và up cả source lên để cho các nhân sự khác sửa",
                    "Thường xuyên hỏi đáp trên nhóm khi thắc mắc"
                ],
                "solution": [
                    "Sửa lại ấn phẩm ngay khi được nhận xét"
                ]
            },
            {
                "id": "AP-003",
                "title": "Thất thoát dữ liệu",
                "level": "critical",
                "description": "File thiết kế bị mất",
                "mitigation": [
                    "Có những file backup, sao lưu liên tục tránh mất mát dữ liệu"
                ],
                "solution": [
                    "Sử dụng file back up"
                ]
            },
            {
                "id": "AP-004",
                "title": "Ấn phẩm bị TBTC, truyền thông, lead trả lại",
                "level": "medium",
                "description": "Ấn phẩm không được duyệt",
                "mitigation": [
                    "Nắm rõ được yêu cầu của BTC về ấn phẩm, concept có liên quan",
                    "Phản hồi tích cực với các feedback được nhận"
                ],
                "solution": [
                    "Sửa lại ấn phẩm ngay khi được nhận xét"
                ]
            }
        ]
    },
    "Game": {
        "Game": [
            {
                "id": "GM-001",
                "title": "Các game chạy không đúng tiến độ, không cuốn hút mọi người",
                "level": "medium",
                "description": "Game không thu hút và không theo timeline",
                "mitigation": [
                    "Thị khảo sơ lược về tâm lý người chơi, testgame để làm timeline hợp lý"
                ],
                "solution": [
                    "Thêm quà, phần thưởng khi hoàn thành minigame, chủ động linh hoạt lại game sao cho bám sát thời gian chơi hết mức có thể"
                ]
            },
            {
                "id": "GM-002",
                "title": "Số lượng người tham gia chơi quá ít",
                "level": "low",
                "description": "Ít người tham gia game",
                "mitigation": [
                    "Truyền thông tích cực, khuyến khích mọi người đăng ký tham gia"
                ],
                "solution": [
                    "Liên hệ sẵn với các CLB thân thiết để tham gia vào trò chơi này, trong thời gian sự kiện diễn ra, MC liên tục remind mọi người về game"
                ]
            },
            {
                "id": "GM-003",
                "title": "Xảy ra xung đột giữa các người chơi",
                "level": "high",
                "description": "Có mâu thuẫn giữa các đội chơi",
                "mitigation": [
                    "Đảm bảo người chơi nắm rõ thể lệ và quy chế thi"
                ],
                "solution": [
                    "Ban giám khảo đứng ra giải quyết xung đột"
                ]
            },
            {
                "id": "GM-004",
                "title": "Số lượng người tham gia chơi quá đông",
                "level": "medium",
                "description": "Quá nhiều người đăng ký chơi",
                "mitigation": [
                    "Giới hạn số đơn đăng ký"
                ],
                "solution": []
            },
            {
                "id": "GM-005",
                "title": "Đội chơi bị loại quá nhiều",
                "level": "low",
                "description": "Nhiều đội bị loại sớm",
                "mitigation": [
                    "Test game từ trước"
                ],
                "solution": [
                    "Cho người chơi tham gia game phụ để có thêm cơ hội chơi"
                ]
            },
            {
                "id": "GM-006",
                "title": "Đội chơi vi phạm luật",
                "level": "medium",
                "description": "Đội chơi không tuân thủ luật chơi",
                "mitigation": [
                    "Thông báo luật cụ thể với các đội chơi"
                ],
                "solution": [
                    "Tùy theo mức độ vi phạm có thể phạt thời gian hoặc loại"
                ]
            },
            {
                "id": "GM-007",
                "title": "Hint, manh mối quá khó cho người tham gia",
                "level": "low",
                "description": "Gợi ý quá khó khiến người chơi không giải được",
                "mitigation": [
                    "Các hint trong trò chơi sẽ được chạy thử một lần để đảm bảo độ khó vừa phải"
                ],
                "solution": [
                    "Đội chơi được phép trừ thời gian của đội mình 5' để đổi lấy đáp án của hint"
                ]
            }
        ]
    },
    "Nhà Tài trợ": {
        "Đối ngoại": [
            {
                "id": "NTT-001",
                "title": "NTT tài trợ quá nhiều hiện vật dư thừa gây thiếu hụt tài trợ hiện kim",
                "level": "high",
                "description": "Tài trợ hiện vật quá nhiều, thiếu tiền mặt",
                "mitigation": [
                    "Trong quá trình trao đổi với NTT chủ động đưa ra những mong muốn về NTT hiện kim"
                ],
                "solution": [
                    "Làm rõ với các NTT về tỉ lệ tài trợ hiện vật (<=50%) và tỉ lệ chuyển đổi tài trợ hiện vật (=30%) trong tổng gói tài trợ"
                ]
            },
            {
                "id": "NTT-002",
                "title": "Nhà tài trợ đột xuất đơn phương hủy hợp đồng",
                "level": "critical",
                "description": "Nhà tài trợ hủy hợp đồng đột ngột",
                "mitigation": [
                    "Trước khi ký hợp đồng cần phải thống nhất trước quyền lợi hiểu rõ về mong muốn của NTT"
                ],
                "solution": [
                    "Làm rõ các điều khoản và trách nhiệm bồi thường của các bên trong trường hợp đơn phương hủy hợp đồng",
                    "Chuẩn bị sẵn các deal tài trợ khẩn cấp và danh sách contact các NTT tiềm năng đã liên hệ trước"
                ]
            },
            {
                "id": "NTT-003",
                "title": "Quyền lợi nhà tài trợ không đúng như trong hồ sơ tài trợ và cam kết trong hợp đồng",
                "level": "high",
                "description": "Quyền lợi không được thực hiện đúng",
                "mitigation": [
                    "Cần tìm hiểu kỹ các quyền lợi NTT đưa ra và trao đổi với BTC trước khi ký hợp đồng"
                ],
                "solution": [
                    "Làm rõ với BTC về các quyền lợi của NTT trong hợp đồng",
                    "Có phương án bổ sung ngay lập tức nếu có thể",
                    "Đàm phán phương án bổ sung quyền lợi cho NTT tùy vào số lượng, loại hình và giá trị của quyền lợi"
                ]
            },
            {
                "id": "NTT-004",
                "title": "Quy mô chương trình, hiệu quả truyền thông hoặc KPI không được như cam kết trong hợp đồng với NTT",
                "level": "high",
                "description": "KPI không đạt như cam kết",
                "mitigation": [
                    "Cần tìm hiểu kỹ các quyền lợi NTT đưa ra và trao đổi với BTC trước khi ký hợp đồng"
                ],
                "solution": [
                    "Làm rõ quy mô tối thiểu (bao nhiêu % so với quy mô dự tính) phải đạt được",
                    "Chuẩn bị nhiều phương án để bổ sung KPI và đàm phán thêm thời gian để hoàn thành KPI sau chương trình",
                    "Bổ sung các mục truyền thông on hoặc off cho NTT sau chương trình"
                ]
            },
            {
                "id": "NTT-005",
                "title": "NTT sử dụng hình ảnh chương trình để quảng bá sản phẩm phản cảm",
                "level": "critical",
                "description": "Nhà tài trợ sử dụng hình ảnh không phù hợp",
                "mitigation": [
                    "Thống nhất trước với đơn vị NTT về những nội dung họ có thể đăng tải",
                    "Tìm hiểu về những đơn vị tài trợ để tránh những đơn vị đã có mâu thuẫn"
                ],
                "solution": [
                    "Làm rõ với NTT về các điều khoản khi quảng bá bằng hình ảnh của chương trình:",
                    "+ NTT chỉ được sử dụng hình ảnh do BTC cung cấp có gắn logo BTC",
                    "+ NTT chỉ được sử dụng hình ảnh Nhãn hàng của mình để PR",
                    "+ NTT không được sử dụng hình ảnh của các nhãn hàng khác để PR dưới mọi hình thức",
                    "+ NTT không được sử dụng hình ảnh chương trình và nhãn hàng khác để truyền thông thiếu khách quan, sai sự thật, bội nhọ"
                ]
            },
            {
                "id": "NTT-006",
                "title": "NTT sử dụng hình ảnh của NTT khác để quảng bá hoặc bội nhọ",
                "level": "critical",
                "description": "Nhà tài trợ vi phạm quy định về hình ảnh",
                "mitigation": [
                    "Thống nhất trước với đơn vị NTT về những nội dung họ có thể đăng tải",
                    "Tìm hiểu về những đơn vị tài trợ để tránh những đơn vị đã có mâu thuẫn"
                ],
                "solution": [
                    "Làm rõ với NTT về các điều khoản khi quảng bá bằng hình ảnh của chương trình:",
                    "+ NTT chỉ được sử dụng hình ảnh do BTC cung cấp có gắn logo BTC",
                    "+ NTT chỉ được sử dụng hình ảnh Nhãn hàng của mình để PR",
                    "+ NTT không được sử dụng hình ảnh của các nhãn hàng khác để PR dưới mọi hình thức",
                    "+ NTT không được sử dụng hình ảnh chương trình và nhãn hàng khác để truyền thông thiếu khách quan, sai sự thật, bội nhọ"
                ]
            },
            {
                "id": "NTT-007",
                "title": "Mâu thuẫn giữa NTT và BTC",
                "level": "high",
                "description": "Có mâu thuẫn giữa nhà tài trợ và ban tổ chức",
                "mitigation": [
                    "Thống nhất các quyền lợi từ trước để tránh trường hợp bất đồng quan điểm"
                ],
                "solution": [
                    "Làm rõ với NTT về mọi chi tiết của chương trình và các trường hợp phát sinh dễ xảy ra mâu thuẫn",
                    "Làm rõ với BTC về các yêu cầu của NTT",
                    "Luôn Takecare NTT cẩn thận trong suốt quá trình trong và sau sự kiện",
                    "Luôn luôn bình tĩnh, trao đổi với NTT và BTC nhẹ nhàng để giải quyết"
                ]
            }
        ]
    },
    "Tài chính": {
        "Hậu cần": [
            {
                "id": "TC-001",
                "title": "Tiền chưa kịp giải ngân",
                "level": "high",
                "description": "Tiền chưa được giải ngân kịp thời",
                "mitigation": [
                    "Lên trước kế hoạch tài chính trước ít nhất 2 ngày đi mua đồ, liên hệ với bên tài chính để được giải ngân kịp thời"
                ],
                "solution": [
                    "Tạm ứng trước nhân, sau đó báo lead, tiền của cá nhân sẽ được giải ngân ngay sau khi lead cf"
                ]
            },
            {
                "id": "TC-002",
                "title": "Mất tiền trong lúc đi mua đồ",
                "level": "critical",
                "description": "Tiền bị mất trong quá trình mua sắm",
                "mitigation": [
                    "Chỉ định 1 người cầm tiền, tránh đưa cho nhiều người. (người cầm tiền yêu cầu là người đáng tin cậy)"
                ],
                "solution": [
                    "Ứng trước số tiền của cá nhân. Sau đó làm việc riêng với lead để tìm phương án giải quyết hợp lí"
                ]
            },
            {
                "id": "TC-003",
                "title": "Phát sinh chi phí ngoài kế hoạch",
                "level": "high",
                "description": "Có chi phí phát sinh không nằm trong kế hoạch",
                "mitigation": [
                    "Lên trước kế hoạch tài chính chi tiết, rõ ràng",
                    "Đi khảo giá cụ thể",
                    "Dự trù kinh phí cẩn thận"
                ],
                "solution": [
                    "Sử dụng tiền dự trù, trường hợp vượt quá dự trù thì cần báo cho TBTC để tìm phương án xử lý"
                ]
            },
            {
                "id": "TC-004",
                "title": "Mất hóa đơn",
                "level": "medium",
                "description": "Hóa đơn bị mất, không có để quyết toán",
                "mitigation": [
                    "Chụp hóa đơn ngay sau khi thanh toán xong"
                ],
                "solution": [
                    "Quay lại check với cửa hàng đã mua"
                ]
            }
        ]
    },
    "Vận chuyển": {
        "Hậu cần": [
            {
                "id": "VC-001",
                "title": "Vận chuyển đơn hàng để làm đồ cho sự kiện tới trễ so với dự kiến",
                "level": "high",
                "description": "Hàng hóa không đến đúng hạn",
                "mitigation": [
                    "Lên kế hoạch đặt hàng sớm"
                ],
                "solution": [
                    "Liên hệ với đơn vị vận chuyển để đẩy nhanh tiến độ giao hàng/ ra trực tiếp kho lấy"
                ]
            }
        ]
    },
    "Đồ trang trí": {
        "Hậu cần": [
            {
                "id": "DTT-001",
                "title": "Đồ trang trí bị thiếu",
                "level": "medium",
                "description": "Không đủ đồ trang trí như dự kiến",
                "mitigation": [
                    "Dự trù thêm một lượng đồ trang trí đề phòng thiếu hụt",
                    "Kiểm kê đồ trước khi sử dụng"
                ],
                "solution": [
                    "Tìm nguồn mua đồ trang trí khẩn cấp",
                    "Điều chỉnh cách trang trí với số lượng hiện có"
                ]
            }
        ]
    }
}


def get_risks_by_category(category: str) -> List[Dict[str, Any]]:
    """
    Lấy tất cả risks theo category
    
    Args:
        category: Tên category (e.g., "Cơ sở vật chất", "Nhân sự")
        
    Returns:
        List các risks
    """
    return RISKS_KNOWLEDGE_BASE.get(category, [])


def get_risks_by_owner(owner: str) -> List[Dict[str, Any]]:
    """
    Lấy tất cả risks theo owner (ban phụ trách)
    
    Args:
        owner: Tên ban (e.g., "Takecare", "BTC", "Hậu cần", "takecare", "hậu cần")
        
    Returns:
        List các risks
    """
    all_risks = []
    owner_lower = owner.lower().strip()
    
    # Mapping các tên department variations
    owner_mapping = {
        "takecare": "Takecare",
        "take care": "Takecare",
        "hậu cần": "Hậu cần",
        "hau can": "Hậu cần",
        "hậu cần - thiết công": "Hậu cần",
        "thiết công": "Hậu cần",
        "truyền thông": "Truyền thông",
        "marketing": "Truyền thông",
        "design": "Design",
        "thiết kế": "Design",
        "thiet ke": "Design",
        "media": "Media",
        "nhà ma": "Nhà ma",
        "nha ma": "Nhà ma",
        "đối ngoại": "Đối ngoại",
        "doi ngoai": "Đối ngoại",
        "tài chính": "Tài chính",
        "tai chinh": "Tài chính",
        "game": "Game",
        "nội dung": "Nội dung",
        "noi dung": "Nội dung",
        "btc": "BTC",
        "ban tổ chức": "BTC",
    }
    
    # Normalize owner name
    normalized_owner = owner_mapping.get(owner_lower, owner)
    
    for category, owners in RISKS_KNOWLEDGE_BASE.items():
        for owner_name, risks in owners.items():
            # Exact match
            if owner_name.lower() == owner_lower or owner_name.lower() == normalized_owner.lower():
                all_risks.extend(risks)
            # Partial match (e.g., "hậu cần" matches "Hậu cần")
            elif owner_lower in owner_name.lower() or owner_name.lower() in owner_lower:
                all_risks.extend(risks)
    
    return all_risks


def get_all_risks() -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    """
    Lấy tất cả risks
    
    Returns:
        Dict với structure: {category: {owner: [risks]}}
    """
    return RISKS_KNOWLEDGE_BASE


def search_risks(keyword: str) -> List[Dict[str, Any]]:
    """
    Tìm kiếm risks theo keyword
    
    Args:
        keyword: Từ khóa tìm kiếm
        
    Returns:
        List các risks phù hợp
    """
    keyword_lower = keyword.lower()
    results = []
    
    for category, owners in RISKS_KNOWLEDGE_BASE.items():
        for owner, risks in owners.items():
            for risk in risks:
                # Search in title, description
                if (keyword_lower in risk["title"].lower() or 
                    keyword_lower in risk.get("description", "").lower()):
                    results.append(risk)
    
    return results

