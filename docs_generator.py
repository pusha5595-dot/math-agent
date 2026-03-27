def create_google_doc(docs_service, title, folder_id, drive_service):
    """Creates a new empty Google Doc and moves it into the targeted output folder."""
    # Create the document using Docs API (which bypasses any generic Drive limitations)
    document = docs_service.documents().create(body={'title': title}).execute()
    doc_id = document.get('documentId')
    
    # Move it instantly into the requested folder
    file = drive_service.files().get(fileId=doc_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents', []))
    drive_service.files().update(
        fileId=doc_id,
        addParents=folder_id,
        removeParents=previous_parents,
        fields='id, parents'
    ).execute()
    
    return doc_id

def insert_formatted_text(docs_service, doc_id, text, is_bold=False, has_newline=True, end_index=1):
    """Helper function to format strings with basic styling."""
    if has_newline:
        text += '\n'
    
    requests = [
        {
            'insertText': {
                'location': {'index': end_index},
                'text': text
            }
        }
    ]
    
    if is_bold:
        requests.append({
            'updateTextStyle': {
                'range': {
                    'startIndex': end_index,
                    'endIndex': end_index + len(text)
                },
                'textStyle': {'bold': True},
                'fields': 'bold'
            }
        })
        
    docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    return end_index + len(text)

def generate_doc_from_data(docs_service, doc_id, data):
    """
    Takes the structured ExtractionResult and populates the Google Doc.
    Because the Google Docs API requires inserting text from the end or beginning and adjusting indices,
    we'll construct a large batch update for efficiency.
    """
    requests = []
    current_index = 1
    
    def add_text_request(text, bold=False, empty_lines_after=1):
        nonlocal current_index
        text += '\n' * empty_lines_after
        reqs = [{
            'insertText': {
                'location': {'index': current_index},
                'text': text
            }
        }]
        if bold:
            reqs.append({
                'updateTextStyle': {
                    'range': {
                        'startIndex': current_index,
                        'endIndex': current_index + len(text)
                    },
                    'textStyle': {'bold': True},
                    'fields': 'bold'
                }
            })
        current_index += len(text)
        return reqs

    if data.exam_name:
        requests.extend(add_text_request(f"Exam Name: {data.exam_name}", bold=True, empty_lines_after=2))

    for i, q in enumerate(data.questions):
        requests.extend(add_text_request(f"Question {i+1}:", bold=True, empty_lines_after=1))
        requests.extend(add_text_request(q.question_text, bold=False, empty_lines_after=2))
        
        requests.extend(add_text_request("Options:", bold=True, empty_lines_after=1))
        for opt in q.options:
            requests.extend(add_text_request(f"• {opt}", bold=False, empty_lines_after=1))
            
        requests.extend(add_text_request("\nCorrect Answer:", bold=True, empty_lines_after=1))
        requests.extend(add_text_request(q.correct_answer, bold=False, empty_lines_after=2))
        
        requests.extend(add_text_request("Explanation:", bold=True, empty_lines_after=1))
        requests.extend(add_text_request(q.explanation, bold=False, empty_lines_after=2))
        
        requests.extend(add_text_request("-" * 40, bold=False, empty_lines_after=2))

    # Execute all requests in batches
    if requests:
        docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
