"""
Makale Üretim Modülü
OpenAI API kullanarak otomatik makale üretimi yapar.
API key yoksa yerleşik şablonlarla makale üretir.
"""

import os
import re
import random
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class ArticleGenerator:
    """Otomatik makale üretici sınıfı."""
    
    TONES = {
        'profesyonel': 'Profesyonel, resmi ve bilgilendirici bir dil kullan.',
        'samimi': 'Samimi, sıcak ve okuyucuyla sohbet eder gibi bir dil kullan.',
        'akademik': 'Akademik, bilimsel ve kaynaklara dayanan bir dil kullan.',
        'seo': 'SEO uyumlu, anahtar kelime odaklı ve web dostu bir dil kullan.',
        'blog': 'Blog yazısı tarzında, kişisel deneyimlerle zenginleştirilmiş bir dil kullan.',
        'haber': 'Haber dili, nesnel ve 5N1K kuralına uygun bir dil kullan.'
    }
    
    LENGTHS = {
        'kisa': (300, 500),
        'orta': (500, 1000),
        'uzun': (1000, 2000),
        'cok_uzun': (2000, 4000)
    }
    
    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY', '')
        self.client = None
        if self.api_key and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
    
    def generate(self, topic, tone='profesyonel', length='orta', 
                 keywords='', target_audience='genel', custom_instructions=''):
        """
        Makale üretir.
        
        Args:
            topic: Makale konusu
            tone: Yazım tonu
            length: Makale uzunluğu
            keywords: Anahtar kelimeler (virgülle ayrılmış)
            target_audience: Hedef kitle
            custom_instructions: Özel talimatlar
            
        Returns:
            dict: {'title': str, 'content': str, 'word_count': int}
        """
        if self.client:
            return self._generate_with_ai(topic, tone, length, keywords, 
                                          target_audience, custom_instructions)
        else:
            return self._generate_with_template(topic, tone, length, keywords,
                                                target_audience)
    
    def _build_prompt(self, topic, tone, length, keywords, target_audience, custom_instructions=''):
        """AI için prompt oluşturur."""
        word_range = self.LENGTHS.get(length, (500, 1000))
        tone_desc = self.TONES.get(tone, self.TONES['profesyonel'])
        
        prompt = f"""Aşağıdaki bilgilere göre Türkçe bir makale yaz:

**Konu:** {topic}
**Yazım Tonu:** {tone_desc}
**Kelime Sayısı:** {word_range[0]} ile {word_range[1]} kelime arasında
**Hedef Kitle:** {target_audience}
"""
        if keywords:
            prompt += f"**Anahtar Kelimeler:** {keywords} (Bu kelimeleri doğal bir şekilde metne yerleştir)\n"
        
        if custom_instructions:
            prompt += f"**Özel Talimatlar:** {custom_instructions}\n"
        
        prompt += """
**Format Kuralları:**
1. Başlık etkileyici ve dikkat çekici olmalı
2. Giriş paragrafı okuyucuyu konuya çekmeli
3. Alt başlıklar kullanarak konuyu bölümlere ayır
4. Her bölümde bilgilendirici ve değerli içerik sun
5. Sonuç paragrafı ile makaleyi toparlayıcı şekilde bitir
6. Markdown formatında yaz (# başlık, ## alt başlık, **kalın** vb.)

Yanıtını şu formatta ver:
BASLIK: [Makale başlığı]
---
[Makale içeriği markdown formatında]
"""
        return prompt
    
    def _generate_with_ai(self, topic, tone, length, keywords, target_audience, custom_instructions):
        """OpenAI API ile makale üretir."""
        prompt = self._build_prompt(topic, tone, length, keywords, target_audience, custom_instructions)
        
        try:
            response = self.client.chat.completions.create(
                model=os.environ.get('OPENAI_MODEL', 'gpt-4o'),
                messages=[
                    {"role": "system", "content": "Sen profesyonel bir Türkçe içerik yazarısın. "
                     "SEO uyumlu, özgün ve kaliteli makaleler yazarsın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content
            return self._parse_result(result_text)
            
        except Exception as e:
            return {
                'title': f'{topic} Hakkında',
                'content': f'Makale üretilirken bir hata oluştu: {str(e)}',
                'word_count': 0,
                'error': str(e)
            }
    
    def _generate_with_template(self, topic, tone, length, keywords, target_audience):
        """Şablon tabanlı makale üretir (API key olmadan)."""
        word_range = self.LENGTHS.get(length, (500, 1000))
        tone_desc = self.TONES.get(tone, 'profesyonel')
        
        # Anahtar kelimeleri listeye çevir
        kw_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else []
        
        title = self._generate_title(topic)
        content = self._generate_template_content(topic, tone, kw_list, target_audience, word_range)
        word_count = len(content.split())
        
        return {
            'title': title,
            'content': content,
            'word_count': word_count
        }
    
    def _generate_title(self, topic):
        """Konu için başlık üretir."""
        templates = [
            f"{topic}: Kapsamlı Bir Rehber",
            f"{topic} Hakkında Bilmeniz Gereken Her Şey",
            f"{topic} Nedir? Detaylı İnceleme",
            f"{topic}: Güncel Bir Değerlendirme",
            f"Adım Adım {topic} Rehberi",
            f"{topic} İçin Eksiksiz Kılavuz",
            f"{topic}: Temel Bilgiler ve İpuçları",
            f"{topic} Dünyasına Giriş"
        ]
        return random.choice(templates)
    
    def _generate_template_content(self, topic, tone, keywords, audience, word_range):
        """Şablon tabanlı içerik üretir."""
        
        sections = []
        
        # Giriş
        intros = [
            f"Günümüzde **{topic}** konusu giderek daha fazla önem kazanmaktadır. "
            f"Bu makalede, {topic} hakkında kapsamlı bir değerlendirme sunacağız.",
            
            f"**{topic}** alanında yaşanan gelişmeler, hem profesyonellerin hem de "
            f"meraklıların dikkatini çekmektedir. Peki {topic} tam olarak nedir ve neden bu kadar önemlidir?",
            
            f"Birçok kişi **{topic}** konusunda yeterli bilgiye sahip değildir. "
            f"Oysa bu konu, günlük hayatımızı doğrudan etkileyen önemli bir alandır."
        ]
        sections.append(random.choice(intros))
        
        # Ana bölümler
        sub_sections = [
            (f"## {topic} Nedir?", [
                f"{topic}, günümüzün en önemli konularından biridir. "
                f"Temel olarak, bu alan birçok farklı disiplini bir araya getirmektedir.",
                f"Bu kavram ilk olarak ortaya çıktığında, sınırlı bir alanda kullanılmaktaydı. "
                f"Ancak zaman içinde kapsamı genişleyerek bugünkü haline ulaşmıştır.",
                f"Uzmanlar, {topic} konusunun önümüzdeki yıllarda daha da önem kazanacağını öngörmektedir."
            ]),
            (f"## {topic} Neden Önemlidir?", [
                f"**{topic}** konusunun önemi birçok faktörden kaynaklanmaktadır. "
                f"Öncelikle, bu alandaki gelişmeler toplumun genelini doğrudan etkilemektedir.",
                f"Araştırmalar göstermektedir ki, {topic} alanında yapılan çalışmalar "
                f"verimlilik ve kalite artışına önemli katkılar sağlamaktadır.",
                f"Ayrıca, {topic} konusundaki yenilikler, sektörde rekabet avantajı "
                f"yaratmak isteyen kuruluşlar için büyük fırsatlar sunmaktadır."
            ]),
            (f"## {topic} ile İlgili Temel Bilgiler", [
                f"Bu bölümde, {topic} hakkında bilmeniz gereken temel noktaları ele alacağız:",
                f"**1. Tarihçe:** {topic} kavramı, uzun bir geçmişe sahiptir ve zaman içinde "
                f"önemli dönüşümler geçirmiştir.",
                f"**2. Güncel Durum:** Bugün itibarıyla {topic} alanında birçok yenilik ve gelişme yaşanmaktadır.",
                f"**3. Gelecek Perspektifi:** Uzmanlar, {topic} konusunun gelecekte daha da "
                f"kritik bir rol oynayacağını değerlendirmektedir."
            ]),
            (f"## {topic} İçin Pratik İpuçları", [
                f"**{topic}** konusunda başarılı olmak için dikkat etmeniz gereken bazı noktalar bulunmaktadır:",
                f"- Güncel gelişmeleri yakından takip edin",
                f"- Alanında uzman kaynaklardan bilgi edinin",
                f"- Teorik bilgiyi pratik uygulamalarla pekiştirin",
                f"- Sürekli öğrenme ve gelişim yaklaşımını benimseyin",
                f"- İlgili topluluklar ve forumlarda aktif olun"
            ]),
            (f"## Sıkça Sorulan Sorular", [
                f"**{topic} ile nasıl başlamalıyım?**\n"
                f"Öncelikle temel kavramları öğrenmek ve güvenilir kaynaklardan bilgi edinmek önemlidir.",
                f"**{topic} alanında kariyer yapılabilir mi?**\n"
                f"Evet, bu alanda birçok farklı kariyer fırsatı bulunmaktadır ve talep giderek artmaktadır.",
                f"**{topic} hakkında hangi kaynakları takip etmeliyim?**\n"
                f"Akademik yayınlar, sektör raporları ve alanında uzman kişilerin paylaşımları "
                f"en güvenilir kaynaklar arasındadır."
            ])
        ]
        
        # Anahtar kelimeleri bölümlere serpiştir
        for heading, paragraphs in sub_sections:
            section_text = heading + "\n\n"
            for p in paragraphs:
                # Anahtar kelime ekle
                if keywords and random.random() > 0.5:
                    kw = random.choice(keywords)
                    p += f" Bu bağlamda **{kw}** konusu da göz ardı edilmemelidir."
                section_text += p + "\n\n"
            sections.append(section_text)
        
        # Sonuç
        conclusions = [
            f"## Sonuç\n\n"
            f"**{topic}** konusunu detaylı bir şekilde ele aldığımız bu makalede, "
            f"temel kavramlardan pratik ipuçlarına kadar geniş bir perspektif sunduk. "
            f"Unutmayın ki bu alandaki gelişmeler sürekli devam etmektedir ve güncel kalmak büyük önem taşımaktadır.\n\n"
            f"Bu makaleyi faydalı bulduysanız, çevrenizle paylaşmayı unutmayın!",
            
            f"## Sonuç\n\n"
            f"Özetlemek gerekirse, **{topic}** alanı dinamik ve sürekli gelişen bir yapıya sahiptir. "
            f"Bu makalede paylaştığımız bilgi ve öneriler, konuya dair sağlam bir temel oluşturmanıza "
            f"yardımcı olacaktır. Başarıya giden yolda en önemli adım, doğru bilgiye ulaşmak ve "
            f"bunu eyleme dönüştürmektir."
        ]
        sections.append(random.choice(conclusions))
        
        return "\n\n".join(sections)
    
    def _parse_result(self, text):
        """AI yanıtını ayrıştırır."""
        title = ''
        content = text
        
        # BASLIK: formatını ara
        title_match = re.search(r'BASLIK:\s*(.+?)(?:\n|---)', text)
        if title_match:
            title = title_match.group(1).strip()
            # Başlıktan sonraki içeriği al
            separator_pos = text.find('---')
            if separator_pos != -1:
                content = text[separator_pos + 3:].strip()
            else:
                content = text[title_match.end():].strip()
        else:
            # İlk satırı başlık olarak kullan
            lines = text.strip().split('\n')
            if lines:
                title = lines[0].replace('#', '').strip()
                content = '\n'.join(lines[1:]).strip()
        
        word_count = len(content.split())
        
        return {
            'title': title,
            'content': content,
            'word_count': word_count
        }
