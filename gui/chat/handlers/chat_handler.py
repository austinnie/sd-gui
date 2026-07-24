# gui/chat/handlers/chat_handler.py
"""普通对话处理器"""

from .base_handler import BaseHandler


class ChatHandler(BaseHandler):
    """普通对话处理器"""
    
    def handle(self, intent):
        """处理普通对话"""
        text = intent.original_text
        text_lower = text.lower()

        # 检查是否问图片内容
        if self.tab.uploaded_image is not None:
            if any(k in text_lower for k in ['这是什么', '这是什么图片', '描述', '分析']):
                self._handle_image_question()
                return

        # 上下文查询
        if '上下文' in text_lower or 'context' in text_lower:
            summary = self.context_manager.get_summary()
            self._append_message("assistant", f"📊 当前上下文:\n{summary}")
            return

        # 偏好查询
        if '偏好' in text_lower or 'preference' in text_lower:
            self._handle_preference_query()
            return

        # 快速回复
        responses = {
            '你好': '你好！有什么可以帮你的吗？',
            '你是谁': '我是智能生图助手，可以帮助你生成和修改图片。试试说 "生成一张..."！',
            '功能': '我可以：\n• 📝 文生图 - 输入描述生成图片\n• 🖼️ 图生图 - 上传图片并修改\n• 💬 自由对话 - 回答你的问题',
            '帮助': '💡 使用提示：\n• 说 "生成一张..." 来文生图\n• 先上传图片，再说 "改成..." 来图生图\n• 直接聊天也可以',
            '谢谢': '不客气！还有需要帮忙的吗？',
            '再见': '再见！随时回来找我生成图片 😊'
        }

        for key, value in responses.items():
            if key in text_lower:
                self._append_message("assistant", value)
                return

        # 使用 LLM
        if self.tab.llm_enabled_var.get() and self.llm_client.is_available():
            self._append_message("system", "🧠 正在思考...")
            llm_reply = self.llm_client.generate(
                f"用户说：{text}\n请简短友好地回复（一句话，不要超过20字）：",
                timeout=15,
                max_tokens=128
            )
            if llm_reply:
                self._append_message("assistant", llm_reply)
                return

        # 默认回复
        self._append_message("assistant",
            f"🤔 我理解你想说：\"{text}\"\n\n"
            f"如果你想生成图片，可以试试说：\n"
            f"• \"生成一张...\" (文生图)\n"
            f"• 先上传图片，然后说 \"改成...\" (图生图)\n\n"
            f"或者直接告诉我你的需求！")

    def _handle_image_question(self):
        """处理图片相关问题"""
        from gui.chat.utils.image_analyzer import ImageAnalyzer
        
        image_features = ImageAnalyzer.analyze_features(self.tab.uploaded_image_path)
        
        if image_features.get("has_face"):
            self._append_message("assistant",
                f"📷 这张图片包含 {image_features.get('face_count', 0)} 张人脸\n"
                f"📐 尺寸: {image_features.get('width')}x{image_features.get('height')}\n"
                f"{'📱 竖图' if image_features.get('is_portrait') else '🖥️ 横图'}\n\n"
                f"💡 如果你想修改它，请说：\n"
                f"• \"把这张图改成...\"\n"
                f"• \"换成...风格\""
            )
        else:
            self._append_message("assistant",
                f"📷 已上传图片: {os.path.basename(self.tab.uploaded_image_path)}\n"
                f"📐 尺寸: {image_features.get('width')}x{image_features.get('height')}\n\n"
                f"💡 如果你想修改它，请说：\"把这张图改成...\""
            )

    def _handle_preference_query(self):
        """处理偏好查询"""
        prefs = self.context_manager.user_preferences
        pref_list = []
        
        if prefs.get("style"):
            pref_list.append(f"风格: {prefs['style']}")
        if prefs.get("scene"):
            pref_list.append(f"场景: {prefs['scene']}")
        if prefs.get("gender"):
            pref_list.append(f"性别: {prefs['gender']}")

        if pref_list:
            self._append_message("assistant", f"📌 你的偏好:\n• " + "\n• ".join(pref_list))
        else:
            self._append_message("assistant", "📌 还没有记录你的偏好。生成图片时我会自动学习！")