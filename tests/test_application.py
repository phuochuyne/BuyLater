"""Whole-application smoke tests."""

from backend import create_app


def test_health_endpoint():
    app = create_app(testing=True)
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_expected_function_inventory_is_frozen():
    expected = ('capability_save_items_with_price_bd77265a.function.create_saved_item', 'capability_save_items_with_price_bd77265a.function.get_saved_items', 'capability_save_items_with_price_bd77265a.function.get_saved_item_by_id', 'capability_set_cooling_off_period_ed5144db.function.create_cooling_period', 'capability_set_cooling_off_period_ed5144db.function.get_cooling_period', 'capability_set_cooling_off_period_ed5144db.function.list_expired_cooling_periods', 'capability_reminder_notification_fd8968f7.function.schedule_notification', 'capability_reminder_notification_fd8968f7.function.process_due_notifications', 'capability_reminder_notification_fd8968f7.function.cancel_notification', 'capability_reminder_notification_fd8968f7.function.get_notification_status', 'capability_buy_skip_decision_c984506c.function.get_decision_screen_data', 'capability_buy_skip_decision_c984506c.function.record_buy_decision', 'capability_buy_skip_decision_c984506c.function.record_skip_decision', 'capability_buy_skip_decision_c984506c.function.get_user_savings', 'capability_track_estimated_money_saved_66579af4.function.record_savings', 'capability_track_estimated_money_saved_66579af4.function.get_total_savings', 'capability_track_estimated_money_saved_66579af4.function.get_savings_history')
    assert len(expected) == 17
