from api.model.LessonContent import LessonContent
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from api.serializer.ContentHistorySerializer import ContentHistorySerializer
from api.model.ContentHistory import ContentHistory
from api.controllers.permissions.permissions import IsTeacher
from api.controllers.LessonContentController import LessonContentsController
from api.model.Lesson import Lesson
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import FloatField
from django.db.models.functions import Cast

class ContentHistoryController(ModelViewSet):
    queryset = ContentHistory.objects.all()
    serializer_class = ContentHistorySerializer

    # authentication_classes = [SessionAuthentication, TokenAuthentication]

    # def get_permissions(self):
    #     if self.action in ['createHistory', 'getHistoryById']:
    #         return [IsAuthenticated(), IsTeacher()]
    #     else:
    #         return [IsAuthenticated()]
    # allow permission for now

    def createHistoryWithParent(self, request, lesson_id=None, parent_id=None):
        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        content = request.data.get('content')

        try:
            # Check if the lesson exists
            if not Lesson.objects.filter(id=lesson_id).exists():
                return Response({"error": "Lesson does not exist."}, status=status.HTTP_404_NOT_FOUND)

            # Fetch the parent history if provided (i.e., branching from an existing version)
            parent_history = None
            next_child_version = "1"  # Default for a root version if no parent is provided
            
            if parent_id:
                try:
                    parent_history = ContentHistory.objects.get(historyId=parent_id)
                except ContentHistory.DoesNotExist:
                    return Response({"error": "Parent history not found."}, status=status.HTTP_404_NOT_FOUND)

                # Fetch the latest child version of this parent
                latest_child = ContentHistory.objects.filter(parent=parent_history).annotate(
                    version_as_float=Cast('version', FloatField())  # Convert version to float for correct ordering
                ).order_by('-version_as_float').first()

                if latest_child:
                    # If a child exists, increment the last child version (e.g., from 3.1 -> 3.2)
                    parent_version = parent_history.version  # Assuming parent version is a string like "3"
                    last_child_version = latest_child.version  # e.g., "3.1"
                    if '.' in last_child_version:
                        # Increment minor version (e.g., "3.1" -> "3.2")
                        last_minor_version = int(last_child_version.split('.')[1])  # Get the minor version part (e.g., 1 from "3.1")
                        next_child_version = f"{parent_version}.{last_minor_version + 1}"
                    else:
                        # If it's a root version like "3", start from 3.1
                        next_child_version = f"{parent_history.version}.1"
                else:
                    # If no children exist, start with 3.1 (first child)
                    next_child_version = f"{parent_history.version}.1"

            # If no parent, the version stays as 1 or increments for root versions
            elif ContentHistory.objects.filter(lessonId=lesson_id).exists():
                # Fetch latest version and cast it to float for ordering
                latest_version = ContentHistory.objects.filter(lessonId=lesson_id).annotate(
                    version_as_float=Cast('version', FloatField())
                ).order_by('-version_as_float').first()
                next_child_version = str(int(float(latest_version.version)) + 1)  # Increment root version (e.g., 1 -> 2)

            # Create the new ContentHistory with the calculated version
            content_history = ContentHistory.objects.create(
                lessonId_id=lesson_id,
                content=content,
                version=next_child_version,
                parent=parent_history  # Set the parent reference if it exists
            )

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return both serialized data and the historyId
        return Response({
            "historyId": content_history.historyId,
            "data": ContentHistorySerializer(content_history).data
        }, status=status.HTTP_201_CREATED)



    def getHistoryByHistoryId(self, request, history_id=None):

        if not history_id:
            return Response({"error": "history_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the ContentHistory by history_id
            content_history = ContentHistory.objects.get(historyId=history_id)

            # Fetch all children of the content history
            children = ContentHistory.objects.filter(parent=content_history)
            children_serializer = ContentHistorySerializer(children, many=True)

            # Serialize the parent content history
            serializer = ContentHistorySerializer(content_history)

            return Response({
                "parent_history": serializer.data,
                "children": children_serializer.data  # Return the children in the response
            }, status=status.HTTP_200_OK)

        except ContentHistory.DoesNotExist:
            return Response({"error": "ContentHistory not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

    def getAllHistoryByLessonId(self, request, lesson_id=None):

        if not lesson_id:
            return Response({"error": "lesson_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch only parent content histories for the given lesson, ordered by version
        content_histories = ContentHistory.objects.filter(lessonId=lesson_id, parent__isnull=True).annotate(
            version_as_float=Cast('version', FloatField())
        ).order_by('version_as_float')

        histories_with_children = []
        
        for history in content_histories:
            # Fetch children for each content history
            children = ContentHistory.objects.filter(parent=history)
            children_serializer = ContentHistorySerializer(children, many=True)

            # Serialize the parent history
            parent_serializer = ContentHistorySerializer(history)

            # Combine parent and children in the result
            histories_with_children.append({
                "parent_history": parent_serializer.data,
                "children": children_serializer.data
            })

        # Fetch all the lesson contents for the lesson_id and concatenate them into a single string
        current_lesson_contents = LessonContent.objects.filter(lesson_id=lesson_id).order_by('id')
        concatenated_content = '\n'.join([content.contents for content in current_lesson_contents])

        # Return content history with children and the concatenated lesson contents in the response
        return Response({
            'content_histories': histories_with_children,  # All histories and their children
            'current_lesson': concatenated_content  # All lesson contents concatenated into one string
        }, status=status.HTTP_200_OK)


        
    # Restore Version [HttpPut]
    def restoreHistory(self, request, lesson_id=None, history_id=None):
        if not lesson_id or not history_id:
            return Response({"error": "Both lesson_id and history_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the specific history based on lesson_id and history_id
            content_history = ContentHistory.objects.filter(lessonId=lesson_id, historyId=history_id).first()
            if not content_history:
                return Response({"error": "Content history not found."}, status=status.HTTP_404_NOT_FOUND)

            # Fetch the lesson content for the given lesson_id
            lesson_contents = LessonContent.objects.filter(lesson_id=lesson_id).order_by('id')
            lesson_contents_list = list(lesson_contents)

            # Process the history content via pagination (split by delimiter)
            result = LessonContentsController.split_content_by_delimiter(content_history.content, isRevert=True)
            page_contents = result[1]  # Get array of content pages

            # Log the number of pages for debugging
            print(f"Restoring content: Existing lesson pages = {len(lesson_contents_list)}, History content pages = {len(page_contents)}")

            # Update the existing lesson pages with the content from history
            for index in range(min(len(lesson_contents_list), len(page_contents))):
                lesson_content = lesson_contents_list[index]
                lesson_content.contents = page_contents[index].strip()  # Update content of the page
                lesson_content.save()
                print(f"Updated LessonContent page {index + 1} with content from history")

            # If the history has more pages than the current lesson, create new pages
            if len(page_contents) > len(lesson_contents_list):
                for index in range(len(lesson_contents_list), len(page_contents)):
                    new_lesson_content = LessonContent(
                        lesson_id=lesson_id,
                        contents=page_contents[index].strip()
                    )
                    new_lesson_content.save()
                    print(f"Created new LessonContent page {index + 1} with content from history")

            # After updating/creating pages, check for pages with only <!-- delimiter --> and remove them
            lesson_contents_after = LessonContent.objects.filter(lesson_id=lesson_id).order_by('id')

            for content in lesson_contents_after:
                if content.contents.strip() == "<!-- delimiter -->":
                    print(f"Removing blank page with id {content.id}")
                    content.delete()

            # Success response after restoration
            return Response({"message": "Lesson content restored successfully."}, status=status.HTTP_200_OK)

        except LessonContent.DoesNotExist:
            return Response({"error": "Lesson content not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def updateHistory(self, request, lesson_id=None, history_id=None):

        if not lesson_id or not history_id:
            return Response({"error": "lesson_id and history_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the existing ContentHistory instance
            content_history = ContentHistory.objects.get(pk=history_id, lessonId=lesson_id)

            # Manually update the fields you want to change
            content = request.data.get('content')
            if content is not None:
                content_history.content = content
            
            # You can update other fields here as necessary

            # Save the changes to the database
            content_history.save()

            # Optionally return the updated instance data
            return Response(ContentHistorySerializer(content_history).data, status=status.HTTP_200_OK)

        except ContentHistory.DoesNotExist:
            return Response({"error": "ContentHistory not found."}, status=status.HTTP_404_NOT_FOUND)


    def deleteHistory(self, request, lesson_id=None, history_id=None):
        if not lesson_id or not history_id:
            return Response({"error": "lesson_id and history_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Fetch the parent content history
            content_history = ContentHistory.objects.get(pk=history_id, lessonId=lesson_id)

            # Delete the parent (children will be deleted automatically with CASCADE)
            content_history.delete()

            return Response(status=status.HTTP_204_NO_CONTENT)

        except ContentHistory.DoesNotExist:
            return Response({"error": "ContentHistory not found."}, status=status.HTTP_404_NOT_FOUND)

