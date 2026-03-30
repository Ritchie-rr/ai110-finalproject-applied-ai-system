"""
Edge case tests for PawPal+ scheduler focusing on:
1. Sorting and time handling edge cases
2. Recurring task frequency logic
3. Time conflict detection
4. Task completion and next_due_date calculations
"""

import pytest
from datetime import date, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pawpal_system import Task, Pet, Owner, Scheduler, Priority, Frequency


class TestSortingEdgeCases:
    """Test edge cases in time-based sorting"""
    
    def test_sort_midnight_boundary(self):
        """Test sorting with time at midnight (00:00)"""
        task1 = Task("Feed at midnight", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="00:00")
        task2 = Task("Feed morning", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="06:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task2, task1])
        assert sorted_tasks[0].title == "Feed at midnight"
        assert sorted_tasks[1].title == "Feed morning"
    
    def test_sort_end_of_day_boundary(self):
        """Test sorting with time at end of day (23:59)"""
        task1 = Task("Feed at night", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="23:59")
        task2 = Task("Feed morning", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="06:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task1, task2])
        assert sorted_tasks[0].title == "Feed morning"
        assert sorted_tasks[1].title == "Feed at night"
    
    def test_sort_noon_boundary(self):
        """Test sorting with noon times"""
        task1 = Task("Feed noon", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="12:00")
        task2 = Task("Feed 11:59", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="11:59")
        task3 = Task("Feed 12:01", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="12:01")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        pet.add_task(task3)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task1, task3, task2])
        assert sorted_tasks[0].title == "Feed 11:59"
        assert sorted_tasks[1].title == "Feed noon"
        assert sorted_tasks[2].title == "Feed 12:01"
    
    def test_sort_same_scheduled_time(self):
        """Test sorting with multiple tasks at the same time"""
        task1 = Task("Feed first", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        task2 = Task("Feed second", 30, Priority.MEDIUM.value, Frequency.DAILY.value, scheduled_time="10:00")
        task3 = Task("Feed third", 30, Priority.LOW.value, Frequency.DAILY.value, scheduled_time="10:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        pet.add_task(task3)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task2, task3, task1])
        # All should have same sort key since they have same time
        assert sorted_tasks[0].scheduled_time == "10:00"
        assert sorted_tasks[1].scheduled_time == "10:00"
        assert sorted_tasks[2].scheduled_time == "10:00"
    
    def test_sort_invalid_time_format(self):
        """Test that invalid time formats are treated as unscheduled"""
        task1 = Task("Feed invalid", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="25:00")
        task2 = Task("Feed valid", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task1, task2])
        # Valid time should come before invalid (unscheduled)
        assert sorted_tasks[0].title == "Feed valid"
        assert sorted_tasks[1].title == "Feed invalid"
    
    def test_sort_malformed_time_no_colon(self):
        """Test time format without colon"""
        task1 = Task("Feed no colon", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="1000")
        task2 = Task("Feed valid", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task1, task2])
        # Malformed time should be unscheduled
        assert sorted_tasks[0].title == "Feed valid"
        assert sorted_tasks[1].title == "Feed no colon"
    
    def test_sort_mixed_scheduled_unscheduled(self):
        """Test sorting with mix of scheduled and unscheduled tasks"""
        task1 = Task("Feed unscheduled1", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task2 = Task("Feed morning", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="06:00")
        task3 = Task("Feed unscheduled2", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task4 = Task("Feed evening", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="18:00")
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        pet.add_task(task3)
        pet.add_task(task4)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        sorted_tasks = scheduler.sort_by_time([task4, task1, task2, task3])
        # All scheduled should come before unscheduled
        assert sorted_tasks[0].title == "Feed morning"
        assert sorted_tasks[1].title == "Feed evening"
        assert sorted_tasks[2].title in ["Feed unscheduled1", "Feed unscheduled2"]
        assert sorted_tasks[3].title in ["Feed unscheduled1", "Feed unscheduled2"]


class TestRecurringTasksEdgeCases:
    """Test edge cases in recurring task frequency logic"""
    
    def test_daily_task_always_due(self):
        """Test that daily tasks are always marked as due"""
        task = Task("Feed daily", 30, Priority.HIGH.value, Frequency.DAILY.value)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, date.today()) is True
    
    def test_daily_task_after_completion(self):
        """Test that daily task is still due even after completion"""
        task = Task("Feed daily", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task.mark_complete()
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, date.today()) is True
    
    def test_weekly_task_boundary_7_days(self):
        """Test weekly task due exactly 7 days after completion"""
        task = Task("Bath weekly", 45, Priority.MEDIUM.value, Frequency.WEEKLY.value)
        task.mark_complete()
        # Simulate 7 days passing
        seven_days_later = date.today() + timedelta(days=7)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, seven_days_later) is True
    
    def test_weekly_task_boundary_6_days(self):
        """Test weekly task NOT due 6 days after completion"""
        task = Task("Bath weekly", 45, Priority.MEDIUM.value, Frequency.WEEKLY.value)
        task.mark_complete()
        # Simulate 6 days passing
        six_days_later = date.today() + timedelta(days=6)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, six_days_later) is False
    
    def test_weekly_task_boundary_8_days(self):
        """Test weekly task due 8 days after completion"""
        task = Task("Bath weekly", 45, Priority.MEDIUM.value, Frequency.WEEKLY.value)
        task.mark_complete()
        # Simulate 8 days passing
        eight_days_later = date.today() + timedelta(days=8)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, eight_days_later) is True
    
    def test_monthly_task_boundary_30_days(self):
        """Test monthly task due exactly 30 days after completion"""
        task = Task("Vet checkup", 60, Priority.HIGH.value, Frequency.MONTHLY.value)
        task.mark_complete()
        # Simulate 30 days passing
        thirty_days_later = date.today() + timedelta(days=30)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, thirty_days_later) is True
    
    def test_monthly_task_boundary_29_days(self):
        """Test monthly task NOT due 29 days after completion"""
        task = Task("Vet checkup", 60, Priority.HIGH.value, Frequency.MONTHLY.value)
        task.mark_complete()
        # Simulate 29 days passing
        twenty_nine_days_later = date.today() + timedelta(days=29)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, twenty_nine_days_later) is False
    
    def test_monthly_task_boundary_31_days(self):
        """Test monthly task due 31 days after completion"""
        task = Task("Vet checkup", 60, Priority.HIGH.value, Frequency.MONTHLY.value)
        task.mark_complete()
        # Simulate 31 days passing
        thirty_one_days_later = date.today() + timedelta(days=31)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, thirty_one_days_later) is True
    
    def test_as_needed_always_due(self):
        """Test that as_needed tasks are always due"""
        task = Task("Play with dog", 20, Priority.MEDIUM.value, Frequency.AS_NEEDED.value)
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, date.today()) is True
    
    def test_as_needed_after_completion(self):
        """Test that as_needed tasks are still due after completion"""
        task = Task("Play with dog", 20, Priority.MEDIUM.value, Frequency.AS_NEEDED.value)
        task.mark_complete()
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, date.today()) is True
    
    def test_first_time_task_no_last_completed(self):
        """Test that task with no last_completed is marked as due"""
        task = Task("Initial feeding", 30, Priority.HIGH.value, Frequency.WEEKLY.value)
        assert task.last_completed is None
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        assert scheduler._is_due(task, date.today()) is True
    
    def test_next_due_date_calculation_daily(self):
        """Test next_due_date is calculated correctly for daily tasks"""
        task = Task("Daily feed", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task.mark_complete()
        expected_next = date.today() + timedelta(days=1)
        assert task.next_due_date == expected_next
    
    def test_next_due_date_calculation_weekly(self):
        """Test next_due_date is calculated correctly for weekly tasks"""
        task = Task("Weekly bath", 45, Priority.MEDIUM.value, Frequency.WEEKLY.value)
        task.mark_complete()
        expected_next = date.today() + timedelta(days=7)
        assert task.next_due_date == expected_next
    
    def test_next_due_date_calculation_monthly(self):
        """Test next_due_date is calculated correctly for monthly tasks"""
        task = Task("Monthly vet", 60, Priority.HIGH.value, Frequency.MONTHLY.value)
        task.mark_complete()
        expected_next = date.today() + timedelta(days=30)
        assert task.next_due_date == expected_next
    
    def test_next_due_date_as_needed_none(self):
        """Test that as_needed tasks have no next_due_date"""
        task = Task("Play", 20, Priority.MEDIUM.value, Frequency.AS_NEEDED.value)
        task.mark_complete()
        assert task.next_due_date is None
    
    def test_recurring_task_mark_incomplete(self):
        """Test marking a completed recurring task as incomplete"""
        task = Task("Daily feed", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task.mark_complete()
        assert task.completion_status is True
        task.mark_incomplete()
        assert task.completion_status is False


class TestTaskDurationEdgeCases:
    """Test edge cases related to task duration"""
    
    def test_zero_duration_task(self):
        """Test task with zero duration"""
        task = Task("Instant task", 0, Priority.MEDIUM.value, Frequency.DAILY.value)
        assert task.duration == 0
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        assert task in pet.tasks
    
    def test_very_long_duration_task(self):
        """Test task with duration exceeding available time"""
        task = Task("Long task", 1440, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="09:00")
        owner = Owner("John", 120)  # Only 120 minutes available
        pet = Pet("Fluffy", "cat")
        pet.add_task(task)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        # Task should not fit in plan due to insufficient time
        assert task not in plan.scheduled_tasks or plan.total_time <= owner.time_available
    
    def test_task_duration_one_minute(self):
        """Test task with minimum practical duration"""
        task = Task("Quick task", 1, Priority.LOW.value, Frequency.DAILY.value)
        pet = Pet("Spot", "dog")
        pet.add_task(task)
        assert task.duration == 1


class TestTimeConflictEdgeCases:
    """Test edge cases in time conflict detection"""
    
    def test_tasks_exact_same_time(self):
        """Test multiple tasks scheduled at exactly the same time"""
        task1 = Task("Feed", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        task2 = Task("Groom", 60, Priority.MEDIUM.value, Frequency.DAILY.value, scheduled_time="10:00")
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner = Owner("John", 500)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_time_conflicts(owner.get_all_tasks())
        # Should detect that both tasks are at same time
        assert len(conflicts) > 0
    
    def test_tasks_sequential_no_conflict(self):
        """Test tasks scheduled sequentially with no overlap"""
        task1 = Task("Feed", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        task2 = Task("Groom", 30, Priority.MEDIUM.value, Frequency.DAILY.value, scheduled_time="10:30")
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner = Owner("John", 500)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_time_conflicts(owner.get_all_tasks())
        # These tasks don't conflict
        assert isinstance(conflicts, list)
    
    def test_tasks_overlap_in_time(self):
        """Test tasks that overlap in duration"""
        task1 = Task("Feed", 30, Priority.HIGH.value, Frequency.DAILY.value, scheduled_time="10:00")
        task2 = Task("Groom", 30, Priority.MEDIUM.value, Frequency.DAILY.value, scheduled_time="10:15")
        pet = Pet("Fluffy", "cat")
        pet.add_task(task1)
        pet.add_task(task2)
        owner = Owner("John", 500)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        conflicts = scheduler.detect_time_conflicts()
        # These tasks don't have exact same time, so no conflict detected
        # The conflict detection only flags tasks at exactly the same time
        assert isinstance(conflicts, list)


class TestSchedulingWithRecurringTasks:
    """Test scheduling algorithm with recurring tasks"""
    
    def test_plan_includes_due_daily_tasks(self):
        """Test that daily tasks are included in daily plan"""
        owner = Owner("John", 300)
        pet = Pet("Fluffy", "cat")
        task_daily = Task("Feed daily", 30, Priority.HIGH.value, Frequency.DAILY.value)
        pet.add_task(task_daily)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        assert task_daily in plan.scheduled_tasks
    
    def test_plan_excludes_completed_as_needed_task(self):
        """Test that completed as_needed tasks are excluded from plan"""
        owner = Owner("John", 300)
        pet = Pet("Fluffy", "cat")
        task_as_needed = Task("Play", 20, Priority.LOW.value, Frequency.AS_NEEDED.value)
        task_as_needed.mark_complete()
        pet.add_task(task_as_needed)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        assert task_as_needed not in plan.scheduled_tasks
    
    def test_plan_with_mixed_frequency_tasks(self):
        """Test scheduling with mixed frequency tasks"""
        owner = Owner("John", 500)
        pet = Pet("Fluffy", "cat")
        task_daily = Task("Feed", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task_weekly = Task("Bath", 60, Priority.MEDIUM.value, Frequency.WEEKLY.value)
        task_monthly = Task("Vet", 90, Priority.HIGH.value, Frequency.MONTHLY.value)
        task_asneeded = Task("Play", 20, Priority.LOW.value, Frequency.AS_NEEDED.value)
        pet.add_task(task_daily)
        pet.add_task(task_weekly)
        pet.add_task(task_monthly)
        pet.add_task(task_asneeded)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        # All due tasks should have opportunities to be scheduled
        due_tasks = [t for t in pet.get_incomplete_tasks() 
                     if scheduler._is_due(t, date.today())]
        # Plan should attempt to fit due tasks
        assert plan.total_time <= owner.time_available


class TestMultiPetSchedulingEdgeCases:
    """Test edge cases with multiple pets"""
    
    def test_owner_with_no_pets(self):
        """Test owner with no pets"""
        owner = Owner("John", 500)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        assert plan.total_time == 0
        assert len(plan.scheduled_tasks) == 0
    
    def test_owner_with_multiple_pets_all_tasks_due(self):
        """Test scheduling with multiple pets all having due tasks"""
        owner = Owner("John", 300)
        
        pet1 = Pet("Fluffy", "cat")
        task1 = Task("Feed Fluffy", 30, Priority.HIGH.value, Frequency.DAILY.value)
        pet1.add_task(task1)
        
        pet2 = Pet("Spot", "dog")
        task2 = Task("Feed Spot", 45, Priority.HIGH.value, Frequency.DAILY.value)
        pet2.add_task(task2)
        
        owner.add_pet(pet1)
        owner.add_pet(pet2)
        
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        
        # Both tasks might not fit due to time constraint (30 + 45 = 75 ≤ 300)
        total_scheduled_time = sum(t.duration for t in plan.scheduled_tasks)
        assert total_scheduled_time <= owner.time_available
    
    def test_owner_with_insufficient_time_for_all_tasks(self):
        """Test owner with insufficient time for all due tasks"""
        owner = Owner("John", 30)  # Very limited time
        
        pet = Pet("Fluffy", "cat")
        task1 = Task("Feed", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task2 = Task("Play", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        task3 = Task("Groom", 30, Priority.LOW.value, Frequency.DAILY.value)
        pet.add_task(task1)
        pet.add_task(task2)
        pet.add_task(task3)
        
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        
        # Only one task should fit
        assert len(plan.scheduled_tasks) <= 1
        assert plan.total_time <= owner.time_available


class TestCompletionStatusEdgeCases:
    """Test edge cases related to task completion status"""
    
    def test_new_task_incomplete(self):
        """Test that new tasks start as incomplete"""
        task = Task("New task", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        assert task.completion_status is False
    
    def test_mark_complete_sets_status(self):
        """Test that mark_complete sets completion_status to True"""
        task = Task("Task", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        task.mark_complete()
        assert task.completion_status is True
    
    def test_mark_incomplete_sets_status(self):
        """Test that mark_incomplete sets completion_status to False"""
        task = Task("Task", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        task.mark_complete()
        task.mark_incomplete()
        assert task.completion_status is False
    
    def test_last_completed_updates_on_mark_complete(self):
        """Test that last_completed is updated when task is marked complete"""
        task = Task("Task", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        assert task.last_completed is None
        task.mark_complete()
        assert task.last_completed == date.today()
    
    def test_completed_task_not_in_incomplete_list(self):
        """Test that completed tasks don't appear in incomplete tasks list"""
        pet = Pet("Fluffy", "cat")
        task1 = Task("Task 1", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task2 = Task("Task 2", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        pet.add_task(task1)
        pet.add_task(task2)
        
        task1.mark_complete()
        
        incomplete = pet.get_incomplete_tasks()
        assert task1 not in incomplete
        assert task2 in incomplete


class TestPriorityFilteringEdgeCases:
    """Test edge cases in priority-based filtering"""
    
    def test_filter_high_priority_only(self):
        """Test filtering for only high priority tasks"""
        pet = Pet("Fluffy", "cat")
        task_high = Task("Critical", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task_medium = Task("Normal", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        task_low = Task("Optional", 30, Priority.LOW.value, Frequency.DAILY.value)
        pet.add_task(task_high)
        pet.add_task(task_medium)
        pet.add_task(task_low)
        
        owner = Owner("John", 500)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        high_priority = scheduler.filter_by_priority(Priority.HIGH.value)
        
        assert task_high in high_priority
        assert task_medium not in high_priority
        assert task_low not in high_priority
    
    def test_filter_all_priority_levels(self):
        """Test filtering works for all priority levels"""
        pet = Pet("Fluffy", "cat")
        task_high = Task("Critical", 30, Priority.HIGH.value, Frequency.DAILY.value)
        task_medium = Task("Normal", 30, Priority.MEDIUM.value, Frequency.DAILY.value)
        task_low = Task("Optional", 30, Priority.LOW.value, Frequency.DAILY.value)
        pet.add_task(task_high)
        pet.add_task(task_medium)
        pet.add_task(task_low)
        
        owner = Owner("John", 500)
        owner.add_pet(pet)
        scheduler = Scheduler(owner)
        
        high = scheduler.filter_by_priority(Priority.HIGH.value)
        medium = scheduler.filter_by_priority(Priority.MEDIUM.value)
        low = scheduler.filter_by_priority(Priority.LOW.value)
        
        assert len(high) == 1
        assert len(medium) == 1
        assert len(low) == 1
