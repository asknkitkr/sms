
from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from botocore.exceptions import ClientError
from uuid import uuid4

app = Flask(__name__)
app.secret_key = "student-crud-local-key"

# Connect Python to Floci DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:4567",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

TABLE_NAME = "Students"


def initialize_table():
    try:
        dynamodb.meta.client.describe_table(
            TableName=TABLE_NAME
        )
    except ClientError:
        dynamodb.create_table(
            TableName=TABLE_NAME,
            KeySchema=[
                {
                    "AttributeName": "student_id",
                    "KeyType": "HASH"
                }
            ],
            AttributeDefinitions=[
                {
                    "AttributeName": "student_id",
                    "AttributeType": "S"
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )


initialize_table()
table = dynamodb.Table(TABLE_NAME)


# READ: Display all students
@app.route("/")
def index():
    response = table.scan()
    students = response.get("Items", [])
    return render_template("index.html", students=students)


# CREATE: Add student
@app.route("/add", methods=["POST"])
def add_student():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    course = request.form.get("course", "").strip()

    if not name or not email or not course:
        flash("All fields are required.")
        return redirect(url_for("index"))

    table.put_item(
        Item={
            "student_id": str(uuid4()),
            "name": name,
            "email": email,
            "course": course
        }
    )

    flash("Student added successfully!")
    return redirect(url_for("index"))


# UPDATE: Edit student
@app.route("/edit/<student_id>", methods=["GET", "POST"])
def edit_student(student_id):
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        course = request.form.get("course", "").strip()

        if not name or not email or not course:
            flash("All fields are required.")
            return redirect(url_for(
                "edit_student", student_id=student_id
            ))

        table.update_item(
            Key={"student_id": student_id},
            UpdateExpression="SET #n=:n, email=:e, course=:c",
            ExpressionAttributeNames={"#n": "name"},
            ExpressionAttributeValues={
                ":n": name,
                ":e": email,
                ":c": course
            }
        )

        flash("Student updated successfully!")
        return redirect(url_for("index"))

    response = table.get_item(
        Key={"student_id": student_id}
    )
    student = response.get("Item")

    if not student:
        flash("Student not found.")
        return redirect(url_for("index"))

    return render_template("edit.html", student=student)


# DELETE: Remove student
@app.route("/delete/<student_id>", methods=["POST"])
def delete_student(student_id):
    table.delete_item(
        Key={"student_id": student_id}
    )

    flash("Student deleted successfully!")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
