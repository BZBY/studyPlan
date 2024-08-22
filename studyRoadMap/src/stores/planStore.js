import { defineStore } from 'pinia'

const baseURL = 'http://127.0.0.1:8000'

export const usePlanStore = defineStore('plan', {
  state: () => ({
    plans: [],
    operationHistory: [],
    updateHistory: [],
    planDetails: {},
  }),
  actions: {
    async fetchPlans() {
      try {
        const response = await fetch(`${baseURL}/get_plans`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch plans: ${response.statusText}`);
        }
        const data = await response.json();
        this.plans = data.plans;
      } catch (error) {
        console.error('Failed to fetch plans:', error);
      }
    },

    async fetchPlanDetails(planId) {
      try {
        const response = await fetch(`${baseURL}/get_plan/${planId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch plan details: ${response.statusText}`);
        }
        const data = await response.json();
        this.planDetails = data;
      } catch (error) {
        console.error('Failed to fetch plan details:', error);
      }
    },
    async fetchWeekTasks(weekNumber) {
      try {
        const response = await fetch(`${baseURL}/api/weeks/${weekNumber}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`Failed to fetch tasks for week ${weekNumber}: ${response.statusText}`);
        }

        const data = await response.json();
        this.weekTasks = data;
      } catch (error) {
        console.error(`Failed to fetch tasks for week ${weekNumber}:`, error);
      }
    },

    async addPlan(newPlan) {
      try {
        const response = await fetch(`${baseURL}/add_plan`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(newPlan)
        });
        if (!response.ok) {
          throw new Error(`Failed to add plan: ${response.statusText}`);
        }
        const data = await response.json();
        this.plans.push(newPlan);
        console.log(data.message);
      } catch (error) {
        console.error('Failed to add plan:', error);
      }
    },

    async deletePlan(planId) {
      try {
        const response = await fetch(`${baseURL}/delete_plan/${planId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to delete plan: ${response.statusText}`);
        }
        const data = await response.json();
        this.plans = this.plans.filter(plan => plan.plan_id !== planId);
        console.log(data.message);
      } catch (error) {
        console.error('Failed to delete plan:', error);
      }
    },

    async addTask(task) {
      try {
        const response = await fetch(`${baseURL}/add_task`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(task)
        });
        if (!response.ok) {
          throw new Error(`Failed to add task: ${response.statusText}`);
        }
        const data = await response.json();
        this._addTaskToPlanDetails(task); // 将任务添加到planDetails中
        console.log(data.message);
      } catch (error) {
        console.error('Failed to add task:', error);
      }
    },

    async deleteTask(planId, taskId) {
      try {
        const response = await fetch(`${baseURL}/delete_task/${planId}/${taskId}`, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to delete task: ${response.statusText}`);
        }
        const data = await response.json();
        this._deleteTaskFromPlanDetails(taskId); // 删除planDetails中的任务
        console.log(data.message);
      } catch (error) {
        console.error('Failed to delete task:', error);
      }
    },

    async updateTaskStatus(task) {
      try {
        const response = await fetch(`${baseURL}/update_task_status`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            plan_id: task.plan_id,
            task_id: task.task_id,
            status: task.status,
          }),
        });

        if (!response.ok) {
          throw new Error(`Failed to update task status: ${response.statusText}`);
        }
        const data = await response.json();
        this._updateTaskStatusInPlanDetails(task.task_id, task.status); // 更新planDetails中的任务状态
        console.log(data.message);
      } catch (error) {
        console.error('Failed to update task status:', error);
      }
    },

    async submitComment(planId, taskId, comment) {
      try {
        const response = await fetch(`${baseURL}/submit_comment`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ plan_id: planId, task_id: taskId, comment })
        });
        if (!response.ok) {
          throw new Error(`Failed to submit comment: ${response.statusText}`);
        }
        const data = await response.json();
        this._addCommentToTask(taskId, comment); // 将评论添加到planDetails中的任务
        console.log(data.message);
      } catch (error) {
        console.error('Failed to submit comment:', error);
      }
    },

    async getFeedback(planId, taskId, comment) {
      try {
        const response = await fetch(`${baseURL}/get_feedback`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ plan_id: planId, task_id: taskId, comment })
        });
        if (!response.ok) {
          throw new Error(`Failed to get AI feedback: ${response.statusText}`);
        }
        const data = await response.json();
        this._addFeedbackToTask(taskId, data.feedback); // 将AI反馈添加到planDetails中的任务
        console.log('AI反馈获取成功:', data);
        return data;
      } catch (error) {
        console.error('获取AI反馈失败:', error);
        throw error;
      }
    },

    async editTask(planId, taskId, status,updatedContent) {
      try {
        const response = await fetch(`${baseURL}/edit_task`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ plan_id: planId, task_id: taskId,status:status, updated_task_content: updatedContent })
        });
        if (!response.ok) {
          throw new Error(`Failed to edit task: ${response.statusText}`);
        }
        const data = await response.json();
        this._updateTaskContentInPlanDetails(taskId, updatedContent); // 更新planDetails中的任务内容
        console.log('任务编辑成功:', data.message);
      } catch (error) {
        console.error('任务编辑失败:', error);
      }
    },

    async fetchUpdateHistory(planId) {
      try {
        const response = await fetch(`${baseURL}/get_update_history/${planId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch update history: ${response.statusText}`);
        }
        const data = await response.json();
        this.updateHistory = data.update_history;
      } catch (error) {
        console.error('Failed to fetch update history:', error);
      }
    },

    async fetchOperationHistory(planId) {
      try {
        const response = await fetch(`${baseURL}/get_operation_history/${planId}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        if (!response.ok) {
          throw new Error(`Failed to fetch operation history: ${response.statusText}`);
        }
        const data = await response.json();
        this.operationHistory = data.operation_history;
      } catch (error) {
        console.error('Failed to fetch operation history:', error);
      }
    },

    // 工具方法：在 planDetails 中找到指定的 task，并更新其状态
    _updateTaskStatusInPlanDetails(taskId, status) {
      this._traverseTasks((task) => {
        if (task.task_id === taskId) {
          task.status = status;
        }
      });
    },

    // 工具方法：在 planDetails 中找到指定的 task，并添加评论
    _addCommentToTask(taskId, comment) {
      this._traverseTasks((task) => {
        if (task.task_id === taskId) {
          task.comments.push({
            comment,
            timestamp: new Date().toISOString()
          });
        }
      });
    },

    // 工具方法：在 planDetails 中找到指定的 task，并添加AI反馈
    _addFeedbackToTask(taskId, feedback) {
      this._traverseTasks((task) => {
        if (task.task_id === taskId) {
          task.feedbacks.push({
            feedback,
            timestamp: new Date().toISOString()
          });
        }
      });
    },

    // 工具方法：在 planDetails 中找到指定的 task，并更新其内容
    _updateTaskContentInPlanDetails(taskId, content) {
      this._traverseTasks((task) => {
        if (task.task_id === taskId) {
          task.content = content;
        }
      });
    },

    // 工具方法：遍历所有任务，执行回调函数
    _traverseTasks(callback) {
      this.planDetails.weeks.forEach((week) => {
        week.days.forEach((day) => {
          day.tasks.forEach(callback);
        });
      });
    }
  }
});
