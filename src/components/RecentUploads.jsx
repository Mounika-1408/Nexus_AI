import "./../styles/RecentUploads.css";


function RecentUploads() {

  const uploads = [
    {
      name: "sales_july.csv",
      date: "Today"
    },
    {
      name: "finance_report.xlsx",
      date: "Yesterday"
    },
    {
      name: "inventory.csv",
      date: "2 days ago"
    }
  ];


  return (

    <div className="recent-card">

      <h3>
        Recent Uploads
      </h3>


      <div className="upload-list">

        {
          uploads.map((file,index)=>(

            <div className="upload-item" key={index}>

              <div className="file-icon">
                📄
              </div>


              <div>

                <p className="file-name">
                  {file.name}
                </p>

                <span>
                  {file.date}
                </span>

              </div>


            </div>

          ))
        }

      </div>


    </div>

  );

}


export default RecentUploads;