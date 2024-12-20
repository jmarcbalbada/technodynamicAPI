import json
import re
from datetime import datetime
import traceback
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import api_view
from api.model.Suggestion import Suggestion
from api.serializer.SuggestionSerializer import SuggestionSerializer
from api.serializer.FaqSerializer import FaqSerializer
from api.serializer.LessonContentSerializer import LessonContentSerializer
from api.model.Notification import Notification
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.conf import settings
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationSummaryBufferMemory
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from api.model.Faq import Faq
from rest_framework.decorators import action
from api.model.Lesson import Lesson
from api.model.LessonContent import LessonContent
from api.model.Query import Query
import threading
from django.db import transaction
from django.db.models import Q
import time
from api.model.GroupedQuestions import GroupedQuestions
from api.model.SubQuery import SubQuery
from api.controllers.static.prompts import *
from api.controllers.LessonContentController import LessonContentsController
import openai
from requests.exceptions import HTTPError
import os
from django.views.decorators.csrf import csrf_exempt

class SuggestionController(ModelViewSet):
    queryset = Suggestion.objects.all()
    serializer_class = SuggestionSerializer

    authentication_classes = [SessionAuthentication, TokenAuthentication]

    isRunning = False  # Class-level variable to track background process status


    def insert_delimiter_ai(self, request):
        edited_content = request.data.get('edited_content')
        original_content = request.data.get('original_content')
        lesson_id = request.data.get('lesson_id')
        notification_id = request.data.get('notification_id')

        if not edited_content or not original_content:
            return Response({
                "success": False,
                "message": "Original and edited content are required",
                "data": ""
            }, status=status.HTTP_400_BAD_REQUEST)

        def process_delimiter_task(edited_content, original_content):
        #     # AI prompt preparation
        #     prompt = '''
        #         I wanted you to put delimiter to the edited content base on the original content
        #         **INSTRUCTIONS FOR HANDLING `<!-- delimiter -->` TAGS**
        #         1. **KEEP EXISTING DELIMITERS**
        #         - DO NOT REMOVE ANY EXISTING `<!-- delimiter -->`
        #         2. THE DELIMITER SHOULD ONLY BASE ON THE ORIGINAL CONTENT.
        #         - I WILL BE USING THE DELIMITERS TO SEPARATE THE TEXT IT WILL BE TURNED INTO AN ARRAY SO MAKE SURE TO FOLLOW THE DELIMITER BASED ON THE ORIGINAL CONTENT
        #         - DON'T INCLUDE EVERYTHING IN THE FIRST PAGE FOLLOW THE DELIMITER BASED ON THE ORIGINAL CONTENT
        #         - IMPORTANT RETAIN ALL THE FILE ASSETS AND VIDEOS AND IMAGES< PICTURE LINKS
        #         - **VERY IMPORTANT FOLLOW ALL THE INSTRUCTIONS I WILL DIE IF YOU REPLACE THE EDITED CONTENT I AM ONLY ASKING OF ADDING DELIMITER**
        #         - PLEASE DONT REMOVE ANYTHING I WILL BE DISSAPOINTED
        #         - PLEASE DONT REMOVE ANYTHING I WILL BE DISSAPOINTED
        #
        #         NOTE: IF THERE IS A YOUTUBE LINK VIDEO FROM EDITED CONTENT YOU MUST RETAIN IT AND PUT 1 <br> BELOW IT.
        #         This is the original content """
        #     '''
        #     prompt2 = '''
        #     """
        #         INSTRUCTION: I WANTED YOU TO PUT DELIMITER BASED ON THE ORIGINAL CONTENT
        #
        #         IMPORTANT NOTICE: MAKE SURE TO NOT CHANGE ANY OF THE CONTENT HERE BUT YOU CAN ONLY ADD THE DELIMITER!!!
        #         VERY IMPORTANT NOTE: DO NOT EDIT THE EDITED CONTENT
        #         - IMPORTANT RETAIN ALL THE FILE ASSETS AND VIDEOS AND IMAGES< PICTURE LINKS
        #         - **VERY IMPORTANT FOLLOW ALL THE INSTRUCTIONS I WILL DIE IF YOU REPLACE THE EDITED CONTENT I AM ONLY ASKING OF ADDING DELIMITER**
        #
        #         DON'T MAKE ANY COMMENT JUST REPLY WITH HTML MARKUP, BELOW IS THE EDITED CONTENT:
        #     '''
        #     prompt3 = '''
        #         1. **DELIMITER HANDLING:**
        #         - DO NOT REMOVE or REPLACE the delimiter `<!-- delimiter -->`.
        #         - ONLY SPLIT the content based on the exact occurrence of this delimiter.
        #         - IMPORTANT RETAIN ALL THE FILE ASSETS AND VIDEOS AND IMAGES< PICTURE LINKS
        #
        #         - IMPORTANT RETAIN ALL THE FILE ASSETS AND VIDEOS AND IMAGES< PICTURE LINKS
        #         - **VERY IMPORTANT FOLLOW ALL THE INSTRUCTIONS I WILL DIE IF YOU REPLACE THE EDITED CONTENT I AM ONLY ASKING OF ADDING DELIMITER**
        #
        #         - **FAILURE TO FOLLOW THESE INSTRUCTIONS WILL BREAK THE PROCESS.**
        #     '''
        #     insert_delimiter_ai = 'I will be giving you text in html form and make sure that you will return html form content, make sure to only reply html'
        # #     final_prompt = prompt + original_content + prompt2 + edited_content + prompt3
        #     prompt = '''
        #             I need you to add delimiters to the edited content based on the original content.
        #
        #             **Instructions for Handling `<!-- delimiter -->` Tags**:
        #             1. **Do not remove existing delimiters** (`<!-- delimiter -->`).
        #             2. **Delimiters must match the original content structure**:
        #                 - Use delimiters to separate the text into sections as per the original content.
        #                 - Retain all assets, videos, images, and links.
        #             3. **Do not edit or remove any part of the edited content**:
        #                 - This includes file assets, YouTube links, or images.
        #                 - Add only delimiters where necessary.
        #             4. **YouTube links must be followed by a `<br>` tag**.
        #             5. **your only job is to put delimiter in the edited content and you should try to match where the delimiter of the original content is placced .
        #
        #             Note: Reply with the updated HTML content containing only the added delimiters.
        #         '''
        #
        #     final_prompt = f"{prompt}\n\nOriginal Content:\n{original_content}\n\nEdited Content:\n{edited_content}"
        #
        #     # OpenAI API call
        #     openai.api_key = os.environ.get("OPENAI_API_KEY")
        #     response = openai.ChatCompletion.create(
        #         model="gpt-4",
        #         messages=[
        #             {"role": "system", "content": insert_delimiter_ai},
        #             {"role": "user", "content": final_prompt},
        #         ],
        #         temperature=0.7,
        #     )
        #     ai_response = response['choices'][0]['message']['content'].strip()

            insert_delimiter_ai = "I WILL PROVIDE YOU TEXT IN HTML FORMAT, AND YOU MUST RETURN HTML FORMAT CONTENT. ONLY REPLY WITH HTML."

            prompt = '''
                    I NEED YOU TO ADD DELIMITERS TO THE EDITED CONTENT BASED ON THE ORIGINAL CONTENT.

                    **INSTRUCTIONS FOR HANDLING `<!-- delimiter -->` TAGS**:
                    1. **DO NOT REMOVE EXISTING DELIMITERS** (`<!-- delimiter -->`).
                    2. **DELIMITERS MUST MATCH THE ORIGINAL CONTENT STRUCTURE**:
                        - USE DELIMITERS TO SEPARATE THE TEXT INTO SECTIONS AS PER THE ORIGINAL CONTENT.
                        - RETAIN ALL FILE ASSETS, VIDEOS, IMAGES, AND LINKS EXACTLY AS THEY ARE.
                    3. **DO NOT EDIT OR REMOVE ANY PART OF THE EDITED CONTENT**:
                        - THIS INCLUDES FILE ASSETS, YOUTUBE LINKS, OR IMAGES.
                        - ADD ONLY DELIMITERS WHERE NECESSARY.
                    4. **ENSURE YOUTUBE LINKS ARE FOLLOWED BY A `<br>` TAG**.
                    5. **YOUR ONLY JOB IS TO PLACE DELIMITERS IN THE EDITED CONTENT AND ALIGN THEM WITH THE ORIGINAL CONTENT'S STRUCTURE.**

                    **NOTE**: REPLY ONLY WITH THE UPDATED HTML CONTENT CONTAINING THE DELIMITERS. DO NOT PROVIDE ANY COMMENTS OR EXPLANATIONS.
            '''

            final_prompt = f"{prompt}\n\nORIGINAL CONTENT:\n{original_content}\n\nEDITED CONTENT:\n{edited_content}"

            # OpenAI API call
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": insert_delimiter_ai},
                    {"role": "user", "content": final_prompt},
                ],
                temperature=0.2,
            )
            ai_response = response['choices'][0]['message']['content'].strip()

            # save the response in the suggestion model ai_delimiter
            # You can save `ai_response` to a database or log it
            print("AI Response:", ai_response)

            suggestion = Suggestion.objects.filter(lesson_id=lesson_id, notification_id=notification_id).first()
            if suggestion:
                suggestion.ai_delimiter = ai_response
                suggestion.save()

        # Start the task in a new thread
        thread = threading.Thread(target=process_delimiter_task, args=(edited_content, original_content))
        thread.start()

        return Response({
            "success": True,
            "message": "Processing started. Results will be available later.",
            "data": None
        }, status=status.HTTP_202_ACCEPTED)

    def get_insert_delimiter_ai(self, request):
        lesson_id = request.data.get('lesson_id')
        notification_id = request.data.get('notification_id')

        suggestion = Suggestion.objects.filter(lesson=lesson_id, notification=notification_id).first()
        if suggestion and suggestion.ai_delimiter:
            return Response({
                "success": True,
                "data": suggestion.ai_delimiter
            }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "data": None
        }, status=status.HTTP_200_OK)

    def createInsight(self, request):
        lesson_id = request.data.get('lesson_id')
        notification_id = request.data.get('notification_id')
        
        if not lesson_id or not notification_id:
            return Response({"error": "lesson_id or notification_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # guard lesson and notification check if exists
        print("Checking existing lesson and notification...")
        existing_lesson = Lesson.objects.filter(id=lesson_id).first()
        existing_notification = Notification.objects.filter(notif_id=notification_id).first()

        if not existing_lesson or not existing_notification:
            return Response({"error": "Lesson or Notification does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        # filter suggestion with notif_id 
        print("Suggestion")
        suggestions = Suggestion.objects.filter(lesson_id=lesson_id, notification_id=notification_id)

        if suggestions.exists():
            # If only one suggestion exists, use that suggestion
            existing_suggestion = suggestions.first()
            IsCreated = False
        else:
            # Create a new suggestion
            existing_suggestion = Suggestion.objects.create(lesson_id=lesson_id, notification_id=notification_id)
            IsCreated = True

        # Fetch lesson contents
        print("Fetching lesson contents...")
        lesson_contents = LessonContent.objects.filter(lesson_id=lesson_id)
        
        # Serialize and clean lesson content data
        lesson_content_serializer = LessonContentSerializer(lesson_contents, many=True)
        lesson_content_data = lesson_content_serializer.data

        # Ensure the content field exists in lesson content data
        lesson_content_text = "\n".join([content['contents'] for content in lesson_content_data if 'contents' in content])
        # print("content: ", lesson_content_text)

        # Get grouped questions related to the given notification_id
        print("Fetching grouped questions...")
        grouped_questions = GroupedQuestions.objects.filter(notification_id=notification_id, lesson_id=lesson_id)
        
        # Get FAQs related to these grouped questions
        faqs = Faq.objects.filter(grouped_questions__in=grouped_questions).select_related('grouped_questions__notification')

        # Prepare the response data with only questions
        faq_questions = [faq.question for faq in faqs if faq.grouped_questions and faq.grouped_questions.notification]

        # early return
        if(existing_suggestion.insights is not None):

            if not existing_suggestion.old_content:
                existing_suggestion.old_content = lesson_content_text

            existing_suggestion.save()

            # Reformat faq_questions into bullet points
            formatted_faq_questions = '<p><i>'.join([f"&#8226; {question}" for question in faq_questions]) + '</i></p>'

            response_data = {
                "suggestion": SuggestionSerializer(existing_suggestion).data,
                "faq_questions": formatted_faq_questions
            }

            print("Insight is already created, fetching...")

            if IsCreated:
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response(response_data, status=status.HTTP_200_OK)

        # else create one
        input_text = prompt_create_insights_abs(faq_questions,lesson_content_text)
        
        try:
            # Call OpenAI API to get the suggestion
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SUGGESTION_SYSTEM_CONTENT_INSIGHTS},
                    {"role": "user", "content": input_text}
                ],
                max_tokens=4000,
                temperature=0.7,
            )
            ai_response = response['choices'][0]['message']['content'].strip()

            # Update the existing suggestion with the new insights and old content
            existing_suggestion.insights = ai_response

            if not existing_suggestion.old_content:
                existing_suggestion.old_content = lesson_content_text

            existing_suggestion.save()

            # Reformat faq_questions into bullet points
            formatted_faq_questions = '<p><i>'.join([f"&#8226; {question}" for question in faq_questions]) + '</i></p>'

            response_data = {
                "suggestion": SuggestionSerializer(existing_suggestion).data,
                "faq_questions": formatted_faq_questions
            }

            print("Insight is created now, fetching...")

            if IsCreated:
                return Response(response_data, status=status.HTTP_201_CREATED)
            
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            stack_trace = traceback.format_exc()
            print(f"Error: {str(e)}\nStack Trace:\n{stack_trace}")
            return Response({"error": str(e), "stack_trace": stack_trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def getContentIfExist(self, request):
        lesson_id = request.data.get('lesson_id')
        notification_id = request.data.get('notification_id')

        if not lesson_id or not notification_id:
            return Response({"error": "lesson_id or notification_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Guard: Check if lesson and notification exist
        existing_lesson = Lesson.objects.filter(id=lesson_id).first()
        existing_notification = Notification.objects.filter(notif_id=notification_id).first()

        if not existing_lesson or not existing_notification:
            return Response({"error": "Lesson or Notification does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Check if suggestions exist for the lesson and notification
            existing_suggestions = Suggestion.objects.filter(lesson_id=lesson_id, notification_id=notification_id)

            if existing_suggestions.exists():
                suggestion_with_content = existing_suggestions.filter(content__isnull=False).first()

                if suggestion_with_content:
                    # Prepare response data with content
                    response_data = {
                        'suggestion': SuggestionSerializer([suggestion_with_content], many=True).data,
                        'isPending': False
                    }
                    return Response(response_data, status=status.HTTP_200_OK)

            # No suggestions with content, set isPending=True
            response_data = {
                'suggestion': [],
                'isPending': True
            }
            return Response(response_data, status=status.HTTP_200_OK)  # Changed to 200 OK

        except Exception as e:
            stack_trace = traceback.format_exc()
            return Response({"error": str(e), "stack_trace": stack_trace}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        
    ###--------------------------------------------------------------------------------------------------------###
    #                                                                                                            #
    #    CREATING CONTENTS                                                                                       # 
    #    startBackgroundCreation - starts the process and traverse all the notification and asoociated lessons   #
    #                                                                                                            #
    ###--------------------------------------------------------------------------------------------------------###
    
    @csrf_exempt
    def startBackgroundCreation(self, request):
        """
        Start background content creation process.
        """
        if not self.isRunning:
            self.isRunning = True
            thread = threading.Thread(target=self.createContentForAllNotifications, daemon=True)
            thread.start()
            return Response({"status": "Background content creation started."}, status=status.HTTP_200_OK)
        else:
            return Response({"status": "Background content creation is already running."}, status=status.HTTP_400_BAD_REQUEST)

    def createContentForAllNotifications(self):
        """
        Continuously traverse through all notifications and create or update suggestions.
        Stops when there are no more notifications without suggestions or without content.
        """
        while self.isRunning:
            # Fetch notifications without a suggestion or with a suggestion having no content
            notifications = Notification.objects.filter(
                Q(notification__isnull=True) | Q(notification__content__isnull=True)
            ).distinct()

            if notifications.exists():
                # Process each notification that needs a suggestion
                for notification in notifications:
                    self.createOrUpdateSuggestion(notification)

                # Short sleep to avoid rapid looping (prevents high CPU usage)
                time.sleep(1)

            else:
                # No notifications to process, sleep longer before rechecking
                print("No more notifications to process. Sleeping for 1 minute...")
                time.sleep(15)  # Sleep for 5 minutes before checking again
    # Sleep for 5 minutes before checking again


        # while self.isRunning:
        #     # Fetch notifications that do not have an associated suggestion
        #     notifications = Notification.objects.filter(
        #         notification__isnull=True
        #     )

        #     if notifications.exists():
        #         # Process each notification without a suggestion
        #         for notification in notifications:
        #             self.createOrUpdateSuggestion(notification)
        #     else:
        #         # No more notifications to process, stop the loop
        #         print("No more notifications to process. Stopping background creation.")
        #         self.isRunning = False
        #         break

        #     # Short sleep to avoid rapid looping (prevents high CPU usage)
        #     time.sleep(1)

    def createOrUpdateSuggestion(self, notification):
        """
        Create or update a suggestion for a given notification.
        """
        try:
            lesson = notification.lesson  # Get related lesson from notification
            
            if not lesson:
                return  # Skip if no lesson is related

            # Check if a suggestion already exists for this notification
            suggestion, created = Suggestion.objects.get_or_create(
                lesson=lesson, 
                notification_id=notification.notif_id,
                defaults={'old_content': ''}
            )

            # If suggestion already has content, skip further processing
            if suggestion.content:
                print(f"Suggestion already exists for notification {notification.notif_id}. Skipping...")
                return

            # Fetch lesson contents
            lessonContents = LessonContent.objects.filter(lesson=lesson)
            lessonContentText = "\n".join([content.contents for content in lessonContents])

            # Get grouped questions related to the notification
            groupedQuestions = GroupedQuestions.objects.filter(notification=notification, lesson=lesson)
            faqs = Faq.objects.filter(grouped_questions__in=groupedQuestions).select_related('grouped_questions__notification')
            faqQuestions = [faq.question for faq in faqs if faq.grouped_questions and faq.grouped_questions.notification]

            inputText = prompt_create_content_abs(faqQuestions, lessonContentText)

            # Call OpenAI API to get the suggestion
            openai.api_key = os.environ.get("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SUGGESTION_SYSTEM_CONTENT},
                    {"role": "user", "content": inputText}
                ],
                max_tokens=5700,
                temperature=0.5,
            )
            aiResponse = response['choices'][0]['message']['content'].strip()

            # Update or create the suggestion
            with transaction.atomic():
                suggestion.content = aiResponse
                if not suggestion.old_content:
                    suggestion.old_content = lessonContentText
                suggestion.save()
                print(f"Suggestion created for notification {notification.notif_id}: {suggestion.content}\n\n\n")

        except Exception as e:
            import traceback
            print(f"Error in creating content for notification {notification.notif_id}: {e}")
            traceback.print_exc()
        

    def updateContent(self, request):
        lesson_id = request.data.get('lesson_id')
        new_content = request.data.get('new_content')
        # print("lesson id = ", lesson_id)

        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        # if not new_content:
        #     return Response({"error": "new_content is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Fetch the Suggestion content based on the lesson_id
            suggestion = Suggestion.objects.filter(lesson_id=lesson_id).first()
            if not suggestion:
                return Response({"error": "No suggestion found for the given lesson_id"},
                                status=status.HTTP_404_NOT_FOUND)

            # filtering the yellow and red mark
            # newer_content = self.cleanMarkAiContent(new_content)
            suggestion.content = new_content
            suggestion.save()

            # Process content via pagination (split by delimiter)
            result = LessonContentsController.split_content_by_delimiter(suggestion.content)
            page_contents = result[1]
            # print("Page contents = ", page_contents)

            # Get All Previous Lesson Contents
            prev_contents = LessonContent.objects.filter(lesson_id=lesson_id).order_by('id')
            prev_contents_list = list(prev_contents)

            # print("length")
            # print("page_contents length = ", len(page_contents))
            # print("prev_contents_list length = ", len(prev_contents_list))

            # Update existing pages first
            for index, content in enumerate(page_contents[:len(prev_contents_list)]):
                lesson_content = prev_contents_list[index]
                lesson_content.contents = content.strip()  # Assign content of the page
                lesson_content.save()
                print(f"Updated LessonContent page {index + 1}: {content}")

            # If new content has more pages than the existing ones, create new LessonContent for the extra pages
            if len(page_contents) > len(prev_contents_list):
                for new_index in range(len(prev_contents_list), len(page_contents)):
                    new_content = page_contents[new_index]
                    if new_content.strip():  # Only create new page if content is not empty
                        new_lesson_content = LessonContent(
                            lesson_id=lesson_id,
                            contents=new_content.strip()
                        )
                        new_lesson_content.save()
                        print(f"Created new LessonContent page {new_index + 1}: {new_content}")

            # Delete the LessonContent entries where the contents are just the delimiter (empty pages)
            LessonContent.objects.filter(lesson_id=lesson_id, contents="<!-- delimiter -->").delete()
            print(f"Deleted blank pages with content only as <!-- delimiter -->")

            # If new content has fewer pages, just update existing pages (no deletion allowed)
            return Response({"message": "Content updated successfully"}, status=status.HTTP_200_OK)

        except Lesson.DoesNotExist:
            return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Revert content logic
    def updateRevertContent(self, request):
        lesson_id = request.data.get('lesson_id')
        old_content = request.data.get('old_content')
        # print("lesson id = ", lesson_id)
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the Suggestion content based on the lesson_id
            # suggestion = Suggestion.objects.filter(lesson_id=lesson_id).first()
            # if not suggestion:
            #     return Response({"error": "No suggestion found for the given lesson_id"}, status=status.HTTP_404_NOT_FOUND)

            # old_content = suggestion.old_content
            # if not old_content:
            #     return Response({"error": "No old content found in the suggestion"}, status=status.HTTP_404_NOT_FOUND)
            
            # Split the old_content using the delimiter
            result = LessonContentsController.split_content_by_delimiter(old_content, isRevert=True)
            page_contents = result[1]
            # print("Split old content into pages:", page_contents)

            # Get all the existing LessonContent records for the lesson_id
            lesson_contents = LessonContent.objects.filter(lesson_id=lesson_id).order_by('id')
            lesson_contents_list = list(lesson_contents)

            print(f"Existing pages: {len(lesson_contents_list)}, Reverted content pages: {len(page_contents)}")

            # Update existing pages
            for index in range(min(len(lesson_contents_list), len(page_contents))):
                lesson_content = lesson_contents_list[index]
                lesson_content.contents = page_contents[index].strip()  # Assign the old page content
                lesson_content.save()
                print(f"Updated LessonContent page {index + 1} with old content")

            # If old content has more pages, create new LessonContent for the excess pages
            if len(page_contents) > len(lesson_contents_list):
                for index in range(len(lesson_contents_list), len(page_contents)):
                    new_lesson_content = LessonContent(
                        lesson_id=lesson_id,
                        contents=page_contents[index].strip()
                    )
                    new_lesson_content.save()
                    print(f"Created new LessonContent page {index + 1} with old content")

            return Response({"message": "Lesson content reverted successfully"}, status=status.HTTP_200_OK)

        except LessonContent.DoesNotExist:
            return Response({"error": "Lesson content not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

    def getOldContent(self, request, lesson_id):
        # lesson_id = request.data.get('lesson_id')
        # print("old content lesson id = ", lesson_id)
        # Check if lesson_id is provided
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Fetch the suggestion based on lesson_id
            suggestion = Suggestion.objects.filter(lesson_id=lesson_id).first()

            # Check if a suggestion was found
            if not suggestion:
                return Response({"error": "No suggestion found for the given lesson_id"}, status=status.HTTP_404_NOT_FOUND)

            # Return the old_content
            return Response({"old_content": suggestion.old_content}, status=status.HTTP_200_OK)
        
        except Exception as e:
            # Handle any unexpected errors
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    # delete suggestion and faq related
    def deleteSuggestionByLessonId(self, request):
        lesson_id = request.data.get('lesson_id')
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Delete the Suggestion based on the lesson_id
            suggestion = Suggestion.objects.filter(lesson_id=lesson_id).first()
            if not suggestion:
                return Response({"error": "No suggestion found for the given lesson_id"}, status=status.HTTP_404_NOT_FOUND)
            suggestion.delete()

            # Delete the FAQs based on the lesson_id
            # faqs = Faq.objects.filter(lesson_id=lesson_id)
            # faqs.delete()
            
            return Response({"message": "Suggestion deleted successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
