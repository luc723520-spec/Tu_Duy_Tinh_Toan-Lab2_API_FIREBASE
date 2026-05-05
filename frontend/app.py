from __future__ import annotations

import requests
import streamlit as st
import pandas as pd
from datetime import datetime


BACKEND_BASE_URL = "http://127.0.0.1:8000"
FIREBASE_WEB_API_KEY = "AIzaSyDedJzwRQ_VSlQx-_eQt1j9JhQ3T1-8Rvo"
FIREBASE_SIGN_IN_URL = (
	"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
	f"?key={FIREBASE_WEB_API_KEY}"
)


st.set_page_config(
	page_title="Fitness Tracker",
	page_icon="🏋️‍♂️",
	layout="wide",
	initial_sidebar_state="expanded",
)


def init_session_state() -> None:
	if "logged_in" not in st.session_state:
		st.session_state.logged_in = False
	if "uid" not in st.session_state:
		st.session_state.uid = ""
	if "email" not in st.session_state:
		st.session_state.email = ""


def login_with_firebase(email: str, password: str) -> tuple[bool, str]:
	payload = {
		"email": email,
		"password": password,
		"returnSecureToken": True,
	}

	try:
		response = requests.post(FIREBASE_SIGN_IN_URL, json=payload, timeout=15)
	except requests.RequestException as exc:
		return False, f"Không thể kết nối tới Firebase: {exc}"

	if response.ok:
		data = response.json()
		local_id = data.get("localId")
		if not local_id:
			return False, "Firebase trả về thành công nhưng thiếu localId."

		st.session_state.logged_in = True
		st.session_state.uid = local_id
		st.session_state.email = email
		return True, "Đăng nhập thành công."

	try:
		error_message = response.json().get("error", {}).get("message", "UNKNOWN_ERROR")
	except ValueError:
		error_message = response.text or "UNKNOWN_ERROR"

	return False, f"Đăng nhập thất bại: {error_message}"


def logout() -> None:
	st.session_state.logged_in = False
	st.session_state.uid = ""
	st.session_state.email = ""


def save_meal(uid: str, meat_g: int, eggs_count: int, notes: str) -> tuple[bool, str]:
	payload = {
		"uid": uid,
		"meat_g": meat_g,
		"eggs_count": eggs_count,
		"notes": notes,
	}

	try:
		response = requests.post(f"{BACKEND_BASE_URL}/meals", json=payload, timeout=15)
	except requests.RequestException as exc:
		return False, f"Không thể kết nối tới backend: {exc}"

	if response.ok:
		try:
			return True, response.json().get("message", "Đã lưu bữa ăn thành công.")
		except ValueError:
			return True, "Đã lưu bữa ăn thành công."

	try:
		detail = response.json().get("detail", response.text)
	except ValueError:
		detail = response.text

	return False, f"Lưu thất bại: {detail}"


def fetch_meal_history(uid: str):
	try:
		response = requests.get(f"{BACKEND_BASE_URL}/meals/{uid}", timeout=15)
	except requests.RequestException as exc:
		return False, f"Không thể tải lịch sử: {exc}", []

	if not response.ok:
		try:
			detail = response.json().get("detail", response.text)
		except ValueError:
			detail = response.text
		return False, f"Không thể tải lịch sử: {detail}", []

	try:
		data = response.json().get("data", [])
	except ValueError:
		return False, "Backend trả về dữ liệu không hợp lệ.", []

	return True, "", data


def render_sidebar() -> None:
	st.sidebar.markdown("---")
	st.sidebar.markdown("## 🔐 **Authentication**")
	st.sidebar.markdown("---")

	if st.session_state.logged_in:
		st.sidebar.markdown(f"### ✅ Logged in as")
		st.sidebar.markdown(f"**{st.session_state.email}**")
		st.sidebar.caption(f"User ID: {st.session_state.uid}")
		st.sidebar.markdown("---")
		if st.sidebar.button("🚪 Logout", use_container_width=True, type="secondary"):
			logout()
			st.rerun()
		return

	st.sidebar.markdown("### Login to your account")
	
	with st.sidebar.form("login_form", clear_on_submit=True):
		email = st.text_input("📧 Email", placeholder="your@email.com")
		password = st.text_input("🔑 Password", type="password", placeholder="Enter password")
		submitted = st.form_submit_button("🚀 Login", use_container_width=True, type="primary")

	if submitted:
		if not email or not password:
			st.sidebar.error("⚠️ Please enter both email and password.")
		elif FIREBASE_WEB_API_KEY == "YOUR_WEB_API_KEY":
			st.sidebar.warning("⚠️ Please set your Firebase Web API key.")
		else:
			ok, message = login_with_firebase(email.strip(), password)
			if ok:
				st.sidebar.success(message)
				st.rerun()
			else:
				st.sidebar.error(message)


def render_app() -> None:
	st.markdown("# 🏋️‍♂️ **Fitness Tracker Dashboard**")
	st.markdown("*Track your daily nutrition and build your dream physique*")
	st.divider()

	if not st.session_state.logged_in:
		st.markdown(
			"""
			<div style="text-align: center; padding: 40px;">
			<h3>🔒 Please log in to continue</h3>
			<p>Use the sidebar to sign in with your Firebase account</p>
			</div>
			""",
			unsafe_allow_html=True
		)
		return

	# Display metrics at the top
	history_ok, history_message, history_data = fetch_meal_history(st.session_state.uid)
	
	if history_ok and history_data:
		total_entries = len(history_data)
		total_meat = sum([item.get("meat_g", 0) for item in history_data])
		total_eggs = sum([item.get("eggs_count", 0) for item in history_data])
		
		col1, col2, col3 = st.columns(3)
		with col1:
			st.metric("📊 Total Entries", total_entries, delta=None)
		with col2:
			st.metric("🥩 Total Meat (g)", total_meat, delta=None)
		with col3:
			st.metric("🥚 Total Eggs", total_eggs, delta=None)
		st.divider()

	# Input form section
	st.markdown("## 📝 **Add New Meal Record**")
	
	col1, col2 = st.columns(2)
	with col1:
		meat_val = st.number_input(
			"🥩 Meat (grams)",
			min_value=0,
			value=800,
			step=50,
			help="Enter the amount of meat in grams"
		)
	with col2:
		eggs_val = st.number_input(
			"🥚 Eggs (count)",
			min_value=0,
			value=5,
			step=1,
			help="Enter the number of eggs"
		)
	
	notes_val = st.text_input(
		"📋 Notes",
		placeholder="Add any additional notes (optional)",
		help="E.g., type of meat, cooking method, etc."
	)
	
	col_btn1, col_btn2 = st.columns([1, 3])
	with col_btn1:
		submitted = st.button("🚀 Submit", use_container_width=True, type="primary")
	
	if submitted:
		ok, message = save_meal(
			uid=st.session_state.uid,
			meat_g=int(meat_val),
			eggs_count=int(eggs_val),
			notes=notes_val,
		)
		if ok:
			st.success(f"✅ {message}")
			st.rerun()
		else:
			st.error(f"❌ {message}")

	st.divider()

	# History section with enhanced visualization
	st.markdown("## 📈 **Meal History & Analytics**")
	
	history_ok, history_message, history_data = fetch_meal_history(st.session_state.uid)
	
	if history_ok:
		if history_data:
			# Convert to DataFrame for better display
			df = pd.DataFrame(history_data)
			
			# Display dataframe with full width
			st.markdown("### 🗂️ **All Records**")
			st.dataframe(df, use_container_width=True, hide_index=True)
			
			# Create visualization if we have data
			if len(df) > 0 and "meat_g" in df.columns:
				st.markdown("### 📊 **Meat Consumption Trend**")
				col_chart1, col_chart2 = st.columns(2)
				
				with col_chart1:
					# Line chart for meat consumption
					meat_chart_data = df[["meat_g"]].copy()
					st.line_chart(meat_chart_data, use_container_width=True)
				
				with col_chart2:
					# Bar chart for egg consumption
					if "eggs_count" in df.columns:
						eggs_chart_data = df[["eggs_count"]].copy()
						st.bar_chart(eggs_chart_data, use_container_width=True)
		else:
			st.info("📭 No meal records yet. Start logging your meals!")
	else:
		st.warning(f"⚠️ {history_message}")


def main() -> None:
	init_session_state()
	render_sidebar()
	render_app()


if __name__ == "__main__":
	main()
