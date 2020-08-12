import React, { FunctionComponent, useState } from "react"
import { Link } from "react-router-dom"
import { student, teacher } from "./Interfaces"

const DashProfile: FunctionComponent<student | teacher> = ({ userName }) => {

    const [logoutMessage, setLogoutMessage] = useState<string>();

    const logout = () => {

        fetch('/api/auth/logout')
        .then(res => res.json()).then(response => {
            setLogoutMessage(response['flashes']);
            console.log(logoutMessage)
        })
    }

    // Get current time in hours:minutes
    const [hour, minute] = new Date().toLocaleTimeString().slice(0, 7).split(":");
    const curTime = hour + ":" + minute;

    // Get day, month, date
    const options = { weekday: "long", month: "long", day: "numeric" };
    const curDate = new Date().toLocaleDateString(undefined, options);

    return (
        <div className="dash-container profile">
            <div className="profile-details">
              <h2>Hello, {userName}</h2>
              <img
                src="https://www.iambetter.org/wp-content/uploads/2020/04/Albert_Einstein_1024x1024.jpg"
                alt="Profile"
                className="profile-pic"
              />
            </div>
            <div className="profile-time">
              <Link to="/" onClick={logout}>
                <i className="material-icons-outlined">exit_to_app</i>
              </Link>
              <Link to="/dashboard">
                <i className="material-icons-outlined">mail</i>
              </Link>
              <h1>{curTime}</h1>
              <p>{curDate}</p>
            </div>
          </div>
    )
}

export default DashProfile