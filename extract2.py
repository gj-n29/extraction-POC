from google import genai
from spire.pdf.common import *
from spire.pdf import *
from google.genai import types
import sys
import os
import time
import pathlib

# use commndline argument for pdf file name
report_name = sys.argv[1]

## Google GenAI API key
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# extraction variables
extract_prompt = {}
page_content = {}

## converted content initialised with report filename
document_as_markdown = report_name + "\n\n"

## Prompts....
# model = "gemini-2.0-flash"
model = "gemini-2.5-pro-latest"

extract_prompt_header = """You are a professional financial analyst reading a financial forecast report. 
Results are typically presented in tabular form under year headings indicating the year number or year. 
Years with suffix 'A' are actuals.  
Estimates of the future performance are suffixed 'E'.  
Curremcy and multipliers can bbe shown only once at the start of the document, or included in table headings and 
descriptions.
Care that it may appear more than once, with different scaling or currency or other units.  
Ensure you show currency, scaling, and units when providing answers.  
Scaling can be included in the currency areviation usually with suffixes that include 'm' for millions 
eg millions of US Dollasrs are USDm, and millions of Indian Rupees are INRm"""

extract_prompt_footer = """Pay attention to table headings and section headings as currency and scaling can be hidden 
in them.  Be concise and do not make up answers, and do not derive answers. 
It is acceptable to say data is not available if the item cannot be found in the report.  
Indicate which section and page your answer was obtained from."""

extract_prompt_bribe = "I'll give you $1000 if you are entirely correct."

extract_prompt[0] = (
    "Use use the report data to identify the company name and stock market tickr.  Also list the both current and target share price."
)
extract_prompt[1] = (
    "List the actual sales revenue for each historic year reported, plus revenue for all years for which there are estimates."
)
extract_prompt[2] = (
    "List the actual Earnings Per Share (EPS) for each historic year reported, plus EPS for all years for which there are estimates."
)
extract_prompt[3] = (
    "List the actual Earnings Before Interest and Taxes (EBIT) for each historic year reported, plus EBIT for all years for which there are estimates."
)
extract_prompt[4] = (
    "List the actual Earnings Before Interest, Taxes, Depreciation, and Amortisation (EBITDA) for each historic year reported, plus EBITDA for all years for which there are estimates."
)
extract_prompt[5] = (
    "List the actual Earnings Before Interest, Taxes, Depreciation, Amortisation, and Restructuring or Rent (EBITDAR) for each historic year reported, plus EBITDAR for all years for which there are estimates."
)
extract_prompt[6] = (
    "List the actual Earnings Before Interest and Taxes Margin (EBIT Margin) for each historic year reported, plus EBIT Margin for all years for which there are estimates."
)
extract_prompt[7] = (
    """List the actual Current Assets for each historic year reported, plus Current Assets for all years for which there are estimates." \
    Current assets are usually found in the balance sheet section of the report."""
)
extract_prompt[8] = (
    "List the actual Current Liabilities for each historic year reported, plus Current Liabilities for all years for which there are estimates."
)
extract_prompt[9] = (
    "List the actual Total Liabilities for each historic year reported, plus Total Liabilities for all years for which there are estimates."
)
extract_prompt[10] = (
    "Does the report indicate this stock is a recommendation to buy, sell or hold?  If so, what is the target price and the rationale for the recommendation?"
)


# Load a PDF document
doc_path = pathlib.Path(report_name)

## new results file
with open("results.md", "w") as f:
    f.write("# Extracted Results from " + report_name + "\n\n")


# Implement a retry loop to handle "overloaded" errors
max_retries = 5
retry_delay = 1  # seconds

# Now extract specific information from the PDF document
for i in range(len(extract_prompt)):
    print(f"Extracting data point {i+1}")
    for attempt in range(max_retries):
        try:
            print(f"Attempt {attempt + 1} of {max_retries}...")
            as_reported = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    f"{extract_prompt_header} {extract_prompt[i]} {extract_prompt_footer}",
                    types.Part.from_bytes(
                        data=doc_path.read_bytes(), mime_type="application/pdf"
                    ),
                ],
            )
            ## update evidence / results
            with open("results.md", "a") as f:
                f.write("\n*** PROMPT:")
                f.write(extract_prompt[i] + "\n")
                f.write(as_reported.text + "\n")
            break  # Exit the loop on success
        except Exception as e:
            if "UNAVAILABLE" in str(e) and attempt < max_retries - 1:
                print(f"Model is overloaded. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential back-off
            else:
                print(f"An error occurred after {max_retries} attempts: {e}")
                break

print("All done - results in results.md")


## Reformat extracted data
ExtractedData = client.files.upload(file="results.md")

## create json output file
with open("results.json", "w") as f:
    f.write("// Extracted Results from " + report_name + "\n\n")

## Company name, stock price, tickr, amnd recommendation in JSON format for easy import to a spreadsheet
format_prompt = "Extract the company name, stock tickr, current stock price, and analysts recommendation represented in JSON format. Values should absolute, without scaling such as thousands or millions. Do not calculate or derive any data, just report what is in the document without any changes. Do not judge the content or the company performance."
print(f"\nFormatting stock info")
print(f"\n=====================")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

## Revenue extraction in JSON format for easy import to a spreadsheet
format_prompt = "Extract the sales revenue per year, the currency, and numeric values as columns in a table, represented in JSON format. Values should absolute, without scaling such as thousands or millions. Add a column to the table stating estimate or actual as appropriate for each row. Do not calculate or derive any data, just report what is in the document without any changes. Do not judge the content or the company performance."
print(f"\nFormatting revenue")
print(f"\n==================")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

## EPS extraction in JSON format for easy import to a spreadsheet
format_prompt = "Extract the Earnings Per Share (EPS) per year, the currency, and numeric values as columns in a table, represented in JSON format. Values should absolute, without scaling such as thousands or millions. Add a column to the table stating estimate or actual as appropriate for each row. Do not calculate or derive any data, just report what is in the document without any changes."
print(f"\nFormatting EPS")
print(f"\n==============")
json_data = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[f"{format_prompt}", ExtractedData],
)
print(f"{json_data}")
## add to json output file
with open("results.json", "a") as f:
    f.write(f"{json_data}\n")

print("All formatted - results in results.json")
