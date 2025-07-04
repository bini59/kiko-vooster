"""
이메일 서비스

학습 리마인더 이메일 발송 및 관리를 담당합니다.
SMTP 또는 외부 이메일 서비스(SendGrid, AWS SES 등)를 통한 이메일 발송을 지원합니다.
"""

import smtplib
import logging
from typing import Optional, Dict, Any, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
from jinja2 import Template
import ssl

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """이메일 발송 서비스"""
    
    def __init__(self):
        """이메일 서비스 초기화"""
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.smtp_use_tls = getattr(settings, 'SMTP_USE_TLS', True)
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@kiko.com')
        self.from_name = getattr(settings, 'FROM_NAME', 'Kiko 일본어 학습')
        
        # SendGrid API 키 (선택적)
        self.sendgrid_api_key = getattr(settings, 'SENDGRID_API_KEY', None)
        
        # 이메일 템플릿 캐시
        self._template_cache = {}
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        action_url: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        이메일을 발송합니다.
        
        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_content: HTML 내용
            text_content: 텍스트 내용 (선택)
            action_url: 액션 버튼 URL (선택)
            template_data: 템플릿 데이터 (선택)
            attachments: 첨부파일 목록 (선택)
            
        Returns:
            발송 성공 여부
        """
        try:
            # SendGrid 사용 가능하면 우선 사용
            if self.sendgrid_api_key:
                return await self._send_via_sendgrid(
                    to_email, subject, html_content, text_content, action_url, template_data
                )
            else:
                return await self._send_via_smtp(
                    to_email, subject, html_content, text_content, action_url, attachments
                )
                
        except Exception as e:
            logger.error(f"이메일 발송 실패: {to_email}, 에러: {e}")
            return False
    
    async def send_learning_reminder(
        self,
        to_email: str,
        user_name: str,
        days_since_last_study: int = 1,
        suggested_study_minutes: int = 30,
        action_url: str = "/study"
    ) -> bool:
        """
        학습 리마인더 이메일을 발송합니다.
        
        Args:
            to_email: 수신자 이메일
            user_name: 사용자 이름
            days_since_last_study: 마지막 학습 후 경과 일수
            suggested_study_minutes: 권장 학습 시간(분)
            action_url: 학습 시작 URL
            
        Returns:
            발송 성공 여부
        """
        try:
            template_data = {
                "user_name": user_name,
                "days_since_last_study": days_since_last_study,
                "suggested_study_minutes": suggested_study_minutes,
                "action_url": action_url
            }
            
            subject = f"{user_name}님, 오늘의 일본어 학습을 시작해보세요! 📚"
            
            html_content = await self._render_learning_reminder_template(template_data)
            text_content = await self._render_learning_reminder_text(template_data)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                action_url=action_url,
                template_data=template_data
            )
            
        except Exception as e:
            logger.error(f"학습 리마인더 이메일 발송 실패: {e}")
            return False
    
    async def send_vocabulary_review_reminder(
        self,
        to_email: str,
        user_name: str,
        review_words_count: int,
        sample_words: List[str],
        action_url: str = "/vocabulary/review"
    ) -> bool:
        """
        단어 복습 리마인더 이메일을 발송합니다.
        
        Args:
            to_email: 수신자 이메일
            user_name: 사용자 이름
            review_words_count: 복습할 단어 수
            sample_words: 샘플 단어 목록
            action_url: 복습 시작 URL
            
        Returns:
            발송 성공 여부
        """
        try:
            template_data = {
                "user_name": user_name,
                "review_words_count": review_words_count,
                "sample_words": sample_words[:5],  # 최대 5개까지만
                "action_url": action_url
            }
            
            subject = f"{user_name}님, {review_words_count}개의 단어가 복습을 기다리고 있어요! 📝"
            
            html_content = await self._render_vocabulary_reminder_template(template_data)
            text_content = await self._render_vocabulary_reminder_text(template_data)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                action_url=action_url,
                template_data=template_data
            )
            
        except Exception as e:
            logger.error(f"단어 복습 리마인더 이메일 발송 실패: {e}")
            return False
    
    async def send_streak_celebration(
        self,
        to_email: str,
        user_name: str,
        streak_days: int,
        action_url: str = "/study"
    ) -> bool:
        """
        연속 학습 축하 이메일을 발송합니다.
        """
        try:
            template_data = {
                "user_name": user_name,
                "streak_days": streak_days,
                "action_url": action_url
            }
            
            subject = f"🔥 {user_name}님, {streak_days}일 연속 학습 달성을 축하합니다!"
            
            html_content = await self._render_streak_template(template_data)
            text_content = await self._render_streak_text(template_data)
            
            return await self.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                action_url=action_url,
                template_data=template_data
            )
            
        except Exception as e:
            logger.error(f"연속 학습 축하 이메일 발송 실패: {e}")
            return False
    
    # =============================================================================
    # SMTP 발송
    # =============================================================================
    
    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        action_url: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """SMTP를 통한 이메일 발송"""
        try:
            # 메시지 생성
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 텍스트 파트 추가
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # HTML 파트 추가
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    await self._add_attachment(msg, attachment)
            
            # SMTP 서버 연결 및 발송
            if self.smtp_use_tls:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    start_tls=True,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
            else:
                await aiosmtplib.send(
                    msg,
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
            
            logger.info(f"SMTP 이메일 발송 성공: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP 이메일 발송 실패: {to_email}, 에러: {e}")
            return False
    
    # =============================================================================
    # SendGrid 발송
    # =============================================================================
    
    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        action_url: Optional[str] = None,
        template_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """SendGrid를 통한 이메일 발송"""
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, From, To, Subject, PlainTextContent, HtmlContent
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            # 메일 객체 생성
            from_email = From(self.from_email, self.from_name)
            to_email = To(to_email)
            subject = Subject(subject)
            
            # 콘텐츠 추가
            content = []
            if text_content:
                content.append(PlainTextContent(text_content))
            content.append(HtmlContent(html_content))
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=text_content,
                html_content=html_content
            )
            
            # 추적 설정
            mail.tracking_settings = {
                "click_tracking": {"enable": True},
                "open_tracking": {"enable": True}
            }
            
            # 발송
            response = sg.send(mail)
            
            if response.status_code in [200, 202]:
                logger.info(f"SendGrid 이메일 발송 성공: {to_email}")
                return True
            else:
                logger.error(f"SendGrid 이메일 발송 실패: {to_email}, 상태코드: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"SendGrid 이메일 발송 실패: {to_email}, 에러: {e}")
            return False
    
    # =============================================================================
    # 템플릿 렌더링
    # =============================================================================
    
    async def _render_learning_reminder_template(self, data: Dict[str, Any]) -> str:
        """학습 리마인더 HTML 템플릿 렌더링"""
        template = """
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>일본어 학습 리마인더</title>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
                .container { max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
                .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
                .header h1 { margin: 0; font-size: 24px; font-weight: 600; }
                .content { padding: 30px; }
                .greeting { font-size: 18px; color: #333; margin-bottom: 20px; }
                .message { font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }
                .cta-button { display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; }
                .cta-button:hover { opacity: 0.9; }
                .footer { background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #6c757d; }
                .stats { background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }
                .stats-item { display: inline-block; margin: 0 15px; text-align: center; }
                .stats-number { font-size: 24px; font-weight: bold; color: #667eea; }
                .stats-label { font-size: 12px; color: #666; text-transform: uppercase; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌸 일본어 학습 시간이에요!</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        안녕하세요 {{ user_name }}님! 👋
                    </div>
                    <div class="message">
                        {{ days_since_last_study }}일 동안 학습하지 않으셨네요. 
                        꾸준한 학습이 실력 향상의 지름길입니다!
                        <br><br>
                        오늘 <strong>{{ suggested_study_minutes }}분</strong>만 투자해서 
                        일본어 실력을 늘려보는 것은 어떨까요?
                    </div>
                    <div class="stats">
                        <div class="stats-item">
                            <div class="stats-number">{{ suggested_study_minutes }}</div>
                            <div class="stats-label">권장 학습시간</div>
                        </div>
                        <div class="stats-item">
                            <div class="stats-number">{{ days_since_last_study }}</div>
                            <div class="stats-label">미학습 일수</div>
                        </div>
                    </div>
                    <div style="text-align: center;">
                        <a href="{{ action_url }}" class="cta-button">
                            지금 바로 학습 시작하기 📚
                        </a>
                    </div>
                </div>
                <div class="footer">
                    <p>Kiko 일본어 학습 플랫폼</p>
                    <p style="font-size: 12px;">
                        이 이메일을 받고 싶지 않다면 
                        <a href="{{ action_url }}/settings">알림 설정</a>에서 변경할 수 있습니다.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        jinja_template = Template(template)
        return jinja_template.render(**data)
    
    async def _render_learning_reminder_text(self, data: Dict[str, Any]) -> str:
        """학습 리마인더 텍스트 템플릿 렌더링"""
        return f"""
안녕하세요 {data['user_name']}님!

{data['days_since_last_study']}일 동안 학습하지 않으셨네요. 
꾸준한 학습이 실력 향상의 지름길입니다.

오늘 {data['suggested_study_minutes']}분만 투자해서 일본어 실력을 늘려보는 것은 어떨까요?

지금 바로 시작하기: {data['action_url']}

---
Kiko 일본어 학습 플랫폼
        """.strip()
    
    async def _render_vocabulary_reminder_template(self, data: Dict[str, Any]) -> str:
        """단어 복습 리마인더 HTML 템플릿 렌더링"""
        sample_words_html = ""
        for word in data['sample_words']:
            sample_words_html += f"<li style='margin: 5px 0; padding: 8px; background-color: #f8f9fa; border-radius: 4px;'>{word}</li>"
        
        template = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>단어 복습 리마인더</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .content {{ padding: 30px; }}
                .greeting {{ font-size: 18px; color: #333; margin-bottom: 20px; }}
                .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                .word-list {{ list-style: none; padding: 0; margin: 20px 0; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-weight: 600; font-size: 16px; text-align: center; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📝 단어 복습 시간!</h1>
                </div>
                <div class="content">
                    <div class="greeting">
                        안녕하세요 {data['user_name']}님! 👋
                    </div>
                    <div class="message">
                        단어장에 <strong>{data['review_words_count']}개</strong>의 단어가 복습 예정입니다. 
                        기억을 되살려 장기 기억으로 만들어보세요!
                    </div>
                    <h3>예정된 복습 단어들:</h3>
                    <ul class="word-list">
                        {sample_words_html}
                    </ul>
                    <div style="text-align: center;">
                        <a href="{data['action_url']}" class="cta-button">
                            지금 복습하기 📚
                        </a>
                    </div>
                </div>
                <div class="footer">
                    <p>Kiko 일본어 학습 플랫폼</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template
    
    async def _render_vocabulary_reminder_text(self, data: Dict[str, Any]) -> str:
        """단어 복습 리마인더 텍스트 템플릿 렌더링"""
        sample_words_text = "\n".join([f"- {word}" for word in data['sample_words']])
        
        return f"""
안녕하세요 {data['user_name']}님!

단어장에 {data['review_words_count']}개의 단어가 복습 예정입니다.
기억을 되살려 장기 기억으로 만들어보세요!

예정된 복습 단어들:
{sample_words_text}

지금 복습하기: {data['action_url']}

---
Kiko 일본어 학습 플랫폼
        """.strip()
    
    async def _render_streak_template(self, data: Dict[str, Any]) -> str:
        """연속 학습 축하 HTML 템플릿 렌더링"""
        template = f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>연속 학습 축하</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
                .header {{ background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); color: #2d3436; padding: 30px; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
                .content {{ padding: 30px; text-align: center; }}
                .streak-number {{ font-size: 48px; font-weight: bold; color: #e17055; margin: 20px 0; }}
                .message {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 30px; }}
                .cta-button {{ display: inline-block; background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%); color: #2d3436; text-decoration: none; padding: 15px 30px; border-radius: 8px; font-weight: 600; font-size: 16px; }}
                .footer {{ background-color: #f8f9fa; padding: 20px; text-align: center; font-size: 14px; color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔥 연속 학습 달성!</h1>
                </div>
                <div class="content">
                    <div class="streak-number">{data['streak_days']}일</div>
                    <div class="message">
                        <strong>{data['user_name']}님!</strong><br>
                        {data['streak_days']}일 연속으로 학습하고 계시네요!<br>
                        정말 대단합니다! 오늘도 연속 기록을 이어가보세요.
                    </div>
                    <a href="{data['action_url']}" class="cta-button">
                        오늘도 학습하기 🌸
                    </a>
                </div>
                <div class="footer">
                    <p>Kiko 일본어 학습 플랫폼</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return template
    
    async def _render_streak_text(self, data: Dict[str, Any]) -> str:
        """연속 학습 축하 텍스트 템플릿 렌더링"""
        return f"""
🔥 연속 학습 달성!

{data['user_name']}님!
{data['streak_days']}일 연속으로 학습하고 계시네요!
정말 대단합니다! 오늘도 연속 기록을 이어가보세요.

오늘도 학습하기: {data['action_url']}

---
Kiko 일본어 학습 플랫폼
        """.strip()
    
    # =============================================================================
    # 유틸리티 메서드
    # =============================================================================
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]):
        """첨부파일을 메시지에 추가"""
        try:
            filename = attachment.get('filename')
            content = attachment.get('content')
            content_type = attachment.get('content_type', 'application/octet-stream')
            
            part = MIMEBase(*content_type.split('/'))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"첨부파일 추가 실패: {e}")
    
    def validate_email(self, email: str) -> bool:
        """이메일 주소 유효성 검증"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def test_smtp_connection(self) -> bool:
        """SMTP 연결 테스트"""
        try:
            if self.smtp_use_tls:
                await aiosmtplib.connect(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    start_tls=True,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
            else:
                await aiosmtplib.connect(
                    hostname=self.smtp_server,
                    port=self.smtp_port,
                    username=self.smtp_username,
                    password=self.smtp_password
                )
            logger.info("SMTP 연결 테스트 성공")
            return True
            
        except Exception as e:
            logger.error(f"SMTP 연결 테스트 실패: {e}")
            return False 