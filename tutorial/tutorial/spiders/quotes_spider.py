import scrapy
import re

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    
    def start_requests(self):
        urls = [
            "https://dethitiengnhat.com/jlpt/N3/202107/1",
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        # Extract all headings with class 'big_item'
        headings = response.css('.big_item')
        
        questions_data = []

        for heading in headings:
            # Get the text content of the current heading
            heading_text = heading.css('::text').get().strip()
            
            # Initialize the list for current heading's questions
            current_questions = []

            # Find all question blocks following the current heading until the next heading
            for sibling in heading.xpath('following-sibling::*'):
                # If a new heading is encountered, stop processing questions for the current heading
                if 'big_item' in sibling.attrib.get('class', ''):
                    break

                # If it's a question block, process it
                if 'question_list' in sibling.attrib.get('class', ''):
                    question_html = sibling.get()  # Preserve the HTML content for each question
                    question_text = self.clean_html_text(question_html)  # Clean up the question text

                    # Extract the question ID
                    question_id = sibling.xpath('following-sibling::div[contains(@id, "diemso")]/@id').get()
                    if question_id:
                        question_id = question_id.replace('diemso', '')
                    else:
                        continue  # Skip if question_id is not found

                    # Extract answers for this question
                    answers = sibling.xpath('following-sibling::div[contains(@class, "answer")][1]')
                    answer_texts = [self.clean_html_text(answer.get()) for answer in answers.css('.answers')]
                    
                    # Extract correct answer
                    correct_answer_id = f'AS{question_id}'
                    correct_answer = response.xpath(f'//div[@id="{correct_answer_id}"]/text()').get()

                    # Append the question details
                    current_questions.append({
                        'question': question_text,
                        'answers': answer_texts,
                        'correct_answer': correct_answer
                    })

            # Append all questions under the current heading
            questions_data.append({
                "heading": heading_text,
                "questions": current_questions
            })

        yield {
            'questions_data': questions_data
        }

    @staticmethod
    def clean_html_text(html):
        """
        Cleans up the HTML text by removing unnecessary spaces while preserving
        the structure and HTML tags like <u>.
        """
        # Normalize whitespace inside tags and between tags
        cleaned_text = re.sub(r'>\s+<', '><', html)  # Remove extra spaces between tags
        cleaned_text = re.sub(r'\s*(<[^>]+>)\s*', r'\1', cleaned_text)  # Remove extra spaces around tags
        return cleaned_text.strip()
