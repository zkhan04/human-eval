import json
import requests

# TODO: move these to a config file or smth
LM_STUDIO_HOST = "localhost"
LM_STUDIO_PORT = 1234

SYSTEM_PROMPT = "You are a coding assistant. Respond ONLY in the request json format. Do not include imports. Do not include additional test cases. Do not include backticks"
IMPORTS = "from typing import List\n\n"

def generate_one_solution(prompt):
  url = f"http://{LM_STUDIO_HOST}:{LM_STUDIO_PORT}/v1/chat/completions"

  headers = {
     "Content-Type": "application/json"
  }

  data = {
     "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt}
     ],
     "response_format": {
        "type": "json_schema",
        "json_schema": {
           "name": "code_repsonse",
           "strict": True,
           "schema": {
              "type": "object",
              "properties": {
                 "code": {
                    "type": "string"
                 }
              },
              "required": ["joke"]
           }
        }
     },
     "temperature": 0.7,
     "max_tokens": -1,
     "stream": False
  }

  try:
     response = requests.post(url, headers=headers, data=json.dumps(data), timeout=60)
     response.raise_for_status()

     result = response.json()
     return json.loads(result['choices'][0]['message']['content'])["code"]
  except requests.exceptions.RequestException as e:
     print(e)
     return None

question_path = "HumanEval.jsonl"
data = []



with open(question_path, 'r') as file:
  for line in file:
      data.append(json.loads(line))

for (i, d) in enumerate(data[:10]):
   out_file = open(f"eval-{i}.py", "w")
   prompt = d["prompt"]
   test = d["test"]
   function_name = d["entry_point"]

   # send the prompt to LMStudio
   completion = generate_one_solution(prompt)

   if completion:
       # removing markdown code formatting
       completion = completion.replace("```python\n", "").replace("```python", "").replace("```", "")
       completion = completion.strip("` \n[")
       
       # remove \\n (double escaped newlines)
       if "\\n" in completion and "\n" not in completion:
           completion = completion.replace("\\n", "\n")
   else:
       completion = "# Failed to generate solution"

   codestring = f"{IMPORTS}{completion}\n\n{test}\n\ncheck({function_name})"
   out_file.write(codestring)

   # My guess is: we have to stitch the prompt and completion together?
   # As well as the included tests, so we have a string that we can pass into exec. Fun!
   # 

   

   # write the solution to some form of external storage / some queue for processing
   # or, just a file for now :) will probably have to run the solutions inside of docker.
