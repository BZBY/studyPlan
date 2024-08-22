import duckdb
import json
import logging

import ollama
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 创建 DuckDB 数据库表
def create_tables():
    with duckdb.connect('file.db') as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS teaching_plan (
            plan_id VARCHAR PRIMARY KEY,
            title TEXT,
            goal TEXT,
            weeks JSON,
            resources JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS task (
            plan_id VARCHAR,
            task_id VARCHAR,
            content TEXT,
            status VARCHAR,
            comments JSON DEFAULT '[]',
            feedbacks JSON DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (plan_id, task_id)
        )
        """)

        con.execute("""
        CREATE TABLE IF NOT EXISTS operation_history (
            plan_id VARCHAR,
            operation_type VARCHAR,
            details JSON,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)


create_tables()


# Pydantic models for request validation
class Comment(BaseModel):
    plan_id: str
    task_id: str
    comment: str


class FeedbackRequest(BaseModel):
    plan_id: str
    task_id: str
    comment: str


class UpdateRequest(BaseModel):
    plan_id: str
    task_id: str
    new_content: str


class EditTask(BaseModel):
    plan_id: str
    status: str
    task_id: str
    updated_task_content: str


class TaskStatusUpdate(BaseModel):
    plan_id: str
    task_id: str
    status: str


class NewPlanJSON(BaseModel):
    plan_id: str
    title: str
    goal: str
    weeks: list
    resources: dict


class NewTask(BaseModel):
    plan_id: str
    task_id: str
    task_content: str


# Log operations
def log_operation(plan_id, operation_type, details):
    with duckdb.connect('file.db') as con:
        try:
            con.execute(
                "INSERT INTO operation_history (plan_id, operation_type, details, timestamp) VALUES (?, ?, ?, CURRENT_TIMESTAMP)",
                (plan_id, operation_type, json.dumps(details)))
        except Exception as e:
            logging.error(f"Failed to log operation: {e}")


# Extract task content
def extract_task_content(md_content, task_id):
    for week in md_content['weeks']:
        for day in week['days']:
            for task in day['tasks']:
                if task['task_id'] == task_id:
                    return task['content']
    return None


@app.get("/get_operation_history/{plan_id}")
def get_operation_history(plan_id: str):
    try:
        with duckdb.connect('file.db') as con:
            if plan_id == "all":
                # Fetch operation history for all plans
                result = con.execute(
                    "SELECT plan_id, operation_type, details, timestamp FROM operation_history").fetchall()
            else:
                # Fetch operation history for a specific plan
                result = con.execute(
                    "SELECT plan_id, operation_type, details, timestamp FROM operation_history WHERE plan_id = ?",
                    (plan_id,)).fetchall()

            # Convert the result to a list of dictionaries
            history = [{
                "plan_id": row[0],
                "operation_type": row[1],
                "details": json.loads(row[2]),
                "timestamp": row[3].isoformat()
            } for row in result]

        return {"operation_history": history}

    except Exception as e:
        logging.error(f"Failed to retrieve operation history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve operation history")


@app.post("/add_plan")
def add_plan(new_plan: NewPlanJSON):
    try:
        with duckdb.connect('file.db') as con:
            con.execute("""
                INSERT INTO teaching_plan (plan_id, title, goal, weeks, resources, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                new_plan.plan_id,
                new_plan.title,
                new_plan.goal,
                json.dumps(new_plan.weeks),
                json.dumps(new_plan.resources)
            ))

        log_operation(new_plan.plan_id, "add", {"message": "Added new teaching plan with JSON content"})
        return {"message": "New teaching plan added successfully"}
    except Exception as e:
        logging.error(f"Failed to add new teaching plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to add new teaching plan")


@app.get("/get_plan/{plan_id}")
def get_plan(plan_id: str):
    try:
        with duckdb.connect('file.db') as con:
            plan_result = con.execute("SELECT title, goal, weeks, resources FROM teaching_plan WHERE plan_id = ?",
                                      (plan_id,)).fetchone()
            if not plan_result:
                raise HTTPException(status_code=404, detail="Teaching plan not found")

            plan_data = {
                "plan_id": plan_id,
                "title": plan_result[0],
                "goal": plan_result[1],
                "weeks": json.loads(plan_result[2]),
                "resources": json.loads(plan_result[3]),
            }

            tasks_result = con.execute(
                "SELECT task_id, content, status, comments, feedbacks FROM task WHERE plan_id = ?",
                (plan_id,)).fetchall()

            tasks_by_week_day = {}
            for task in tasks_result:
                task_id_parts = task[0].split('_')
                week = int(task_id_parts[0].replace('week', ''))
                day = int(task_id_parts[1].replace('day', ''))

                if week not in tasks_by_week_day:
                    tasks_by_week_day[week] = {}
                if day not in tasks_by_week_day[week]:
                    tasks_by_week_day[week][day] = []

                task_data = {
                    "task_id": task[0],
                    "content": task[1],
                    "status": task[2],
                    "comments": json.loads(task[3]),
                    "feedbacks": json.loads(task[4])
                }
                tasks_by_week_day[week][day].append(task_data)

            for week in plan_data["weeks"]:
                week_number = week["week"]
                if week_number in tasks_by_week_day:
                    for day in week["days"]:
                        day_number = day["day"]
                        if day_number in tasks_by_week_day[week_number]:
                            day["tasks"] = tasks_by_week_day[week_number][day_number]

        return plan_data
    except Exception as e:
        logging.error(f"Failed to retrieve plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plan")


@app.delete("/delete_plan/{plan_id}")
def delete_plan(plan_id: str):
    try:
        with duckdb.connect('file.db') as con:
            existing_plan = con.execute("SELECT 1 FROM teaching_plan WHERE plan_id = ?", (plan_id,)).fetchone()
            if not existing_plan:
                raise HTTPException(status_code=404, detail="Plan not found")

            con.execute("DELETE FROM teaching_plan WHERE plan_id = ?", (plan_id,))
            con.execute("DELETE FROM task WHERE plan_id = ?", (plan_id,))

        log_operation(plan_id, "delete", {"message": "Deleted teaching plan"})
        return {"message": "Teaching plan deleted successfully"}
    except Exception as e:
        logging.error(f"Failed to delete plan: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete plan")


@app.get("/api/weeks/{week_number}")
def get_week_tasks(week_number: int):
    try:
        with duckdb.connect('file.db') as con:
            # 查询所有计划中包含的周数据
            plans_result = con.execute("SELECT plan_id, title, weeks FROM teaching_plan").fetchall()

            tasks_by_day = {}

            for plan in plans_result:
                plan_id = plan[0]
                plan_title = plan[1]
                weeks = json.loads(plan[2])

                # 查找匹配的周
                for week in weeks:

                    if week["week"] == week_number:
                        for day in week["days"]:
                            while day["day"] > 7:
                                day["day"] -= 7
                            day_number = day["day"]

                            if day_number not in tasks_by_day:
                                tasks_by_day[day_number] = []

                            for task in day["tasks"]:
                                task_data = {
                                    "task_id": task["task_id"],
                                    "content": task["content"],
                                    "status": task["status"],
                                    "comments": task.get("comments", []),
                                    "feedbacks": task.get("feedbacks", []),
                                    "plan_id": plan_id,
                                    "plan_title": plan_title
                                }
                                tasks_by_day[day_number].append(task_data)

            # 组织返回的周数据结构
            week_data = {
                "week": week_number,
                "days": []
            }
            print("????")
            print(tasks_by_day)
            for day in range(1, 8):  # 1-7代表周一到周日
                day_data = {
                    "day": day,
                    "tasks": tasks_by_day.get(day, [])
                }
                week_data["days"].append(day_data)

        if not week_data["days"]:
            raise HTTPException(status_code=404, detail=f"No tasks found for week {week_number}")

        return week_data

    except Exception as e:
        logging.error(f"Failed to retrieve tasks for week {week_number}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@app.post("/add_task")
def add_task(new_task: NewTask):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the existing 'weeks' JSON structure
            plan_result = con.execute("SELECT weeks FROM teaching_plan WHERE plan_id = ?",
                                      (new_task.plan_id,)).fetchone()

            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            weeks = json.loads(plan_result[0])

            # Parse task_id to get week and day info (assuming task_id format is weekN_dayM_taskX)
            task_id_parts = new_task.task_id.split('_')
            week_number = int(task_id_parts[0].replace('week', ''))
            day_number = int(task_id_parts[1].replace('day', ''))

            # Find the specific week and day to add the task
            week_found = False
            day_found = False
            for week in weeks:
                if week["week"] == week_number:
                    week_found = True
                    for day in week["days"]:
                        if day["day"] == day_number:
                            day["tasks"].append({
                                "task_id": new_task.task_id,
                                "content": new_task.task_content,
                                "status": "Pending",
                                "comments": [],
                                "feedbacks": []
                            })
                            day_found = True
                            break
                    break

            if not week_found or not day_found:
                raise HTTPException(status_code=404, detail="Week or Day not found in plan")

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), new_task.plan_id))

        log_operation(new_task.plan_id, "add_task", {
            "task_id": new_task.task_id,
            "content": new_task.task_content,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"message": "Task added successfully"}

    except Exception as e:
        logging.error(f"Failed to add task: {e}")
        raise HTTPException(status_code=500, detail="Failed to add task")


@app.delete("/delete_task/{plan_id}/{task_id}")
def delete_task(plan_id: str, task_id: str):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the existing 'weeks' JSON structure
            plan_result = con.execute("SELECT weeks FROM teaching_plan WHERE plan_id = ?",
                                      (plan_id,)).fetchone()

            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            weeks = json.loads(plan_result[0])

            # Parse task_id to get week and day info
            task_id_parts = task_id.split('_')
            week_number = int(task_id_parts[0].replace('week', ''))
            day_number = int(task_id_parts[1].replace('day', ''))

            # Find the specific week and day to delete the task
            task_deleted = False
            for week in weeks:
                if week["week"] == week_number:
                    for day in week["days"]:
                        if day["day"] == day_number:
                            day["tasks"] = [task for task in day["tasks"] if task["task_id"] != task_id]
                            task_deleted = True
                            break
                    break

            if not task_deleted:
                raise HTTPException(status_code=404, detail="Task not found in plan")

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), plan_id))

        log_operation(plan_id, "delete_task", {
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"message": "Task deleted successfully"}

    except Exception as e:
        logging.error(f"Failed to delete task: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete task")


@app.get("/get_plans")
def get_plans():
    try:
        with duckdb.connect('file.db') as con:
            result = con.execute("SELECT plan_id, title FROM teaching_plan").fetchall()
        plans = [{"plan_id": row[0], "title": row[1]} for row in result]
        return {"plans": plans}
    except Exception as e:
        logging.error(f"Failed to retrieve plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve plans")


@app.post("/submit_comment")
def submit_comment(comment: Comment):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the existing 'weeks' JSON structure
            plan_result = con.execute("SELECT weeks FROM teaching_plan WHERE plan_id = ?",
                                      (comment.plan_id,)).fetchone()
            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            weeks = json.loads(plan_result[0])

            # Locate the specific task to add a comment
            task_found = False
            for week in weeks:
                for day in week["days"]:
                    for task in day["tasks"]:
                        if task["task_id"] == comment.task_id:
                            task["comments"].append({
                                "comment": comment.comment,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            task_found = True
                            break
                    if task_found:
                        break
                if task_found:
                    break

            if not task_found:
                raise HTTPException(status_code=404, detail="Task not found in plan")

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), comment.plan_id))

        log_operation(comment.plan_id, "submit_comment", {
            "task_id": comment.task_id,
            "comment": comment.comment,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"message": "Comment submitted successfully"}

    except Exception as e:
        logging.error(f"Failed to submit comment: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit comment")


@app.post("/get_feedback")
def get_feedback(feedback_request: FeedbackRequest):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the teaching plan's JSON data
            plan_result = con.execute("SELECT title, goal, weeks FROM teaching_plan WHERE plan_id = ?",
                                      (feedback_request.plan_id,)).fetchone()
            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            # Convert the weeks JSON string to a Python dictionary
            weeks = json.loads(plan_result[2])

            # Locate the specific task to generate feedback
            task_content = None
            for week in weeks:
                for day in week["days"]:
                    for task in day["tasks"]:
                        if task["task_id"] == feedback_request.task_id:
                            task_content = task["content"]
                            break
                    if task_content:
                        break
                if task_content:
                    break

            if not task_content:
                raise HTTPException(status_code=404,
                                    detail=f"Task content not found for task_id: {feedback_request.task_id}")

            # Call the AI model to generate feedback
            response = ollama.chat(model='llama3.1', messages=[
                {
                    "role": "user",
                    "content": (
                        f"现在你是一个教授编程开发的高级教师，现在我给你一份学习计划数据: {json.dumps({'title': plan_result[0], 'goal': plan_result[1], 'weeks': weeks}, ensure_ascii=False)}，"
                        f"这是我感到疑问的任务点: {task_content}，然后这是我的评论: {feedback_request.comment}，"
                        "现在我希望你能给我合适的建议来帮助我更好的学习,具体建议内容请包裹在&&&{{code}}&&&中发给我。"
                    )
                }
            ])

            # Extract the feedback from the AI response
            feedback = response['message']['content']

            # Append the new feedback to the task
            feedbacks_appended = False
            for week in weeks:
                for day in week["days"]:
                    for task in day["tasks"]:
                        if task["task_id"] == feedback_request.task_id:
                            task["feedbacks"].append({
                                "feedback": feedback,
                                "timestamp": datetime.utcnow().isoformat()
                            })
                            feedbacks_appended = True
                            break
                    if feedbacks_appended:
                        break
                if feedbacks_appended:
                    break

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), feedback_request.plan_id))

        log_operation(feedback_request.plan_id, "get_feedback", {
            "task_id": feedback_request.task_id,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"feedback": feedback}

    except Exception as e:
        logging.error(f"Failed to get feedback: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feedback")


@app.put("/update_task_status")
def update_task_status(update_request: TaskStatusUpdate):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the existing 'weeks' JSON structure
            plan_result = con.execute("SELECT weeks FROM teaching_plan WHERE plan_id = ?",
                                      (update_request.plan_id,)).fetchone()

            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            weeks = json.loads(plan_result[0])

            # Locate the specific task by task_id
            task_found = False
            for week in weeks:
                for day in week["days"]:
                    for task in day["tasks"]:
                        if task["task_id"] == update_request.task_id:
                            # Update the task's status
                            task["status"] = update_request.status
                            task_found = True
                            break
                    if task_found:
                        break
                if task_found:
                    break

            if not task_found:
                raise HTTPException(status_code=404, detail="Task not found in plan")

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), update_request.plan_id))

        # Log the operation if needed
        log_operation(update_request.plan_id, "update_task_status", {
            "task_id": update_request.task_id,
            "status": update_request.status,
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"message": "Task status updated successfully"}

    except Exception as e:
        logging.error(f"Failed to update task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update task status")


from datetime import datetime


def serialize_datetime(obj):
    """Convert datetime objects to strings in ISO format."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_db_to_json(db_path, output_file):
    try:
        # Connect to the DuckDB database
        with duckdb.connect(db_path) as con:
            # Get the list of tables
            tables = con.execute("SHOW TABLES").fetchall()

            # Initialize a dictionary to store the database contents
            db_data = {}

            # Iterate over each table
            for table in tables:
                table_name = table[0]
                # Fetch all data from the table
                table_data = con.execute(f"SELECT * FROM {table_name}").fetchall()

                # Get column names for the table
                columns = con.execute(f"PRAGMA table_info({table_name})").fetchall()
                column_names = [column[1] for column in columns]

                # Convert the data to a list of dictionaries
                db_data[table_name] = [dict(zip(column_names, row)) for row in table_data]

            # Export the database data to a JSON file with datetime handling
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(db_data, f, indent=4, ensure_ascii=False, default=serialize_datetime)

            print(f"Database exported successfully to {output_file}")
    except Exception as e:
        print(f"Failed to export database: {e}")


export_db_to_json('file.db', 'db_export.json')


@app.post("/edit_task")
def edit_task(edit_request: EditTask):
    try:
        with duckdb.connect('file.db') as con:
            # Retrieve the existing 'weeks' JSON structure
            plan_result = con.execute("SELECT weeks FROM teaching_plan WHERE plan_id = ?",
                                      (edit_request.plan_id,)).fetchone()

            if not plan_result:
                raise HTTPException(status_code=404, detail="Plan not found")

            weeks = json.loads(plan_result[0])

            # Locate the specific task
            task_found = False
            for week in weeks:
                for day in week["days"]:
                    for task in day["tasks"]:
                        if task["task_id"] == edit_request.task_id:
                            # Update task details
                            task["content"] = edit_request.updated_task_content
                            task["status"] = edit_request.status or task["status"]
                            task_found = True
                            break
                    if task_found:
                        break
                if task_found:
                    break

            if not task_found:
                raise HTTPException(status_code=404, detail="Task not found in plan")

            # Update the 'weeks' structure in the database
            con.execute("""
                UPDATE teaching_plan 
                SET weeks = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE plan_id = ?
            """, (json.dumps(weeks), edit_request.plan_id))

        log_operation(edit_request.plan_id, "edit_task", {
            "task_id": edit_request.task_id,
            "updated_task_data": {
                "content": edit_request.updated_task_content,
                "status": edit_request.status,
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        return {"message": "Task updated successfully"}

    except Exception as e:
        logging.error(f"Failed to edit task: {e}")
        raise HTTPException(status_code=500, detail="Failed to edit task")


# 启动 FastAPI 应用
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backdb:app", host="127.0.0.1", port=8000, reload=True)
