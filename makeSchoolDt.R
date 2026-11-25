rm(list=ls())
library(dplyr)
library(data.table)
library(ggplot2)
library(stringr)
library(geojsonio)
library(broom)
library(rjson)
library(sf)
library(suncalc)




#===========================#
####      function       ####
#===========================#


makeSchoolDt <- function (rawSv.dt, spdf, gps.dt) {
  Sv.dt <- rawSv.dt
  Sv.dt <- Sv.dt[complete.cases(Sv.dt)]
  
  #== calculate depth_bin of pixel ==#
  setDT(Sv.dt)[, depth_bin := (DepthStop- DepthStart)/SampleCount]
  setDT(Sv.dt)[, depthStart := DepthStart + (depth_bin * (as.numeric(gsub("Sv", "", SampleNo))-1))]
  setDT(Sv.dt)[, depthStop := depthStart + depth_bin]
  
  #== recalculate RangeStop  ==#
  #Sv.dt[vessel %in% c("SD1031", "SD1032"), RangeStop := max(depthStop), by = .(PingNumber, vessel, id)]
  
  
  #== calculate sV from SV ==#
  setDT(Sv.dt)[, sV := 10^(Sv/10)]
  
  #== frequency response by each ping & each sample  ==#
  setDT(Sv.dt)[, sV38 := sV[Frequency==38], by = c("id", "PingNumber", "SampleNo", "vessel")]
  
  #== frequency response by school id use mean sV of school  ==#
  setDT(Sv.dt)[, sV_mean := mean(sV, na.rm = TRUE), by = c("id", "Frequency", "vessel")][, rf := sV_mean/sV_mean[Frequency==38], by = c("id", "vessel")]
  setDT(Sv.dt)[, sV_max := max(sV, na.rm = TRUE), by = c("id", "Frequency", "vessel")][, sV_min := min(sV, na.rm = TRUE), by = c("id", "Frequency", "vessel")]
  setDT(Sv.dt)[, PingNo := max(PingNumber)-min(PingNumber) + 1, by =c("id", "vessel")][, sV_stdv := sd(sV, na.rm = TRUE), by = c("id", "Frequency", "vessel")]
  setDT(Sv.dt)[, SE_f := sV_stdv/sqrt(PingNo*SampleCount), by = c("id", "Frequency", "vessel")][, SE := SE_f/mean(sV38), by = c("id", "Frequency", "vessel")] #standard error
  setDT(Sv.dt)[, sV_var := var(sV, na.rm = TRUE), by = c("id", "Frequency", "vessel")]
  setDT(Sv.dt)[, pixelNo := length(sV), by = c("id", "Frequency", "vessel")]
  
  #== time ==#
  setDT(Sv.dt)[,da:=paste(stringr::str_sub(Date, 1,4), stringr::str_sub(Date, 5,6), stringr::str_sub(Date, 7,8), sep="-")]
  setDT(Sv.dt)[,Time:=as.integer(Time)][,Time := (ifelse(nchar(Time)==7, paste0("0", Time), Time))]
  setDT(Sv.dt)[,Time := (ifelse(nchar(Time)==6, paste0("00", Time), Time))][,Time := (ifelse(nchar(Time)==5, paste0("000", Time), Time))][,Time := (ifelse(nchar(Time)==4, paste0("0000", Time), Time))][,Time := (ifelse(nchar(Time)==3, paste0("00000", Time), Time))]
  setDT(Sv.dt)[,t:=paste(stringr::str_sub(Time, -8,-7), stringr::str_sub(Time, -6,-5), stringr::str_sub(Time, -4,-3), sep=":")][,t:=paste(t, stringr::str_sub(Time, -2,-1), sep=".")]
  setDT(Sv.dt)[,YMD_time:=paste(da, t, sep=" ")][,YMD_time:=as.POSIXct(YMD_time, "%Y-%m-%d %H:%M:%S", tz= "UTC")][,da:=NULL][,t:=NULL]
  
  #== Distance between pings ==#
  #bottom.dt <- as.data.table(bottom.json)
  bottom.dt <- data.table(PingNumber = gps.dt$PingNumber,
                          PingDistance = gps.dt$PingDistance,
                          BottomDepth = gps.dt$BottomDepth,
                          vessel = gps.dt$vessel)
  setDT(bottom.dt)[, Diff:=c(0, diff(bottom.dt$PingDistance))][, distance:= Diff*1852][,Diff:=NULL][,PingDistance:=NULL]
  setDT(bottom.dt)[, BottomDepth := zoo::na.approx(BottomDepth), by = vessel]
  
  #== School size(area), School length ==#
  Sv.dt <- merge(x = Sv.dt, y = bottom.dt, by = c("PingNumber", "vessel"), all.x = TRUE)
  setDT(Sv.dt)[, pixel_size := distance*depth_bin]
  setDT(Sv.dt)[, school_area := sum(pixel_size), by = c("id", "Frequency", "vessel")][,school_length := distance/.N, by = c("id", "Frequency","PingNumber", "vessel")][, school_length := sum(school_length), by = c("id", "Frequency", "vessel")]
  
  #== sA calculation ==#
  setDT(Sv.dt)[, sV_nmi := sV*4*pi*(1852)^2][, sV_nmi := sV_nmi * depth_bin] # multiplying depth bin (0.177m) compute sA of each pixel.
  setDT(Sv.dt)[, sA := sum(sV_nmi)/PingNo, by = c("id", "Frequency", "vessel")]
  
  #== mean depth ==#
  setDT(Sv.dt)[, meanDepth := mean(c(DepthStart, DepthStop)), by=c("id", "Frequency", "vessel")]
  #setDT(Sv.dt)[, sV_nmi_sample := mean(sV_nmi), by=c("id", "Frequency", "SampleNo", "vessel")]#[, sA2 := sum(sV_nmi_sample)/PingNo, by=c("id", "Frequency")]
  setDT(Sv.dt)[, sV_nmi_sample := sum(sV_nmi), by=c("id", "Frequency", "SampleNo", "vessel")]
  
  
  wmd.dt <- data.table()
  
  for(v in  unique(Sv.dt$vessel)){
    
    id <- unique(Sv.dt[vessel %in% v]$id)
    Sv.temp <- Sv.dt[vessel %in% v]
    temp2 <- data.table()
    
    for(i in id) {
      temp <- Sv.temp[id %in% i]
      temp <- dplyr::select(temp, depthStop, depth_bin,  Frequency, SampleNo, sV_nmi_sample)
      temp[, depth.mean := depthStop - (depth_bin/2), by=c("Frequency", "SampleNo")]
      temp <- temp[ ,list(depth = mean(depth.mean), sV_nmi_sample = mean(sV_nmi_sample)), by = c("Frequency", "SampleNo")]
      temp$id <- i
      temp2 <- rbind(temp2, temp)
    }
    temp2$vessel <- v
    wmd.dt <- rbind(wmd.dt, temp2)
    
  }
  
  wmd.dt <- setDT(wmd.dt)
  wmd.dt[, weighted_meanDepth := weighted.mean(depth, sV_nmi_sample), by=c("id", "Frequency", "vessel")]
  wmd.dt <- dplyr::select(wmd.dt, Frequency, id, vessel, weighted_meanDepth )
  wmd.dt <- wmd.dt[!duplicated(wmd.dt)]
  
  Sv.dt <- merge(x = Sv.dt, y = wmd.dt, by = c("id", "vessel", "Frequency"), all.x = TRUE)
  #setDT(Sv.dt)[, weighted_meanDepth := weighted.mean((depthStop - (depth_bin/2)), sV_nmi_sample), by=c("id", "Frequency", "PingNumber", "vessel")]
  
  
  #== depth from bottom ==#
  setDT(Sv.dt)[, DepthfromBottom := max(BottomDepth) - weighted_meanDepth, by=c("id", "Frequency", "vessel")]
  setDT(Sv.dt)[, nor_Depth := weighted_meanDepth/max(BottomDepth), by=c("id", "Frequency", "vessel")]
  setDT(Sv.dt)[, nor_DepthStart := DepthStart/BottomDepth][, nor_DepthStop := ifelse(DepthStop/max(BottomDepth, na.rm = TRUE)>1 , 1 , DepthStop/max(BottomDepth, na.rm = TRUE)), by=c("id","Frequency", "vessel")]
  setDT(Sv.dt)[, BottomAltitude := BottomDepth - max(depthStop) + (depth_bin/2), by=c("PingNumber", "id", "Frequency", "vessel")]
  setDT(Sv.dt)[, BottomAltitude := ifelse(BottomAltitude < 0, NA, BottomAltitude)]
  setDT(Sv.dt)[, BottomAltitude := min(BottomAltitude, na.rm = TRUE), by=c("id", "Frequency", "vessel")]
  
  
  #== Perimeter ==#
  Sv.dt[, yoko := lapply(.SD, function(x) c(1, diff(x))), .SDcols = "SampleNo", by = list(id, Frequency, PingNumber, vessel)]
  Sv.dt[, yoko2 := ifelse(yoko!=1,distance*2, 0)][, yoko3 := sum(yoko2)+distance*2, by=c("id", "Frequency", "PingNumber", "vessel")]
  Sv.dt[, yoko4 := yoko3/.N, by=c("id", "Frequency","PingNumber", "vessel")][,yoko5:=sum(yoko4),  by=c("id", "Frequency", "vessel")][,yoko:=NULL][,yoko2:=NULL][,yoko3:=NULL][,yoko4:=NULL]
  Sv.dt[, tate := c(1, diff(PingNumber)), by=c("id", "Frequency", "SampleNo", "vessel")][, tate2 := ifelse(tate!=1, depth_bin*2, 0)][, tate3:=sum(tate2)+depth_bin*2, by=c("id", "Frequency", "SampleNo", "vessel")]
  Sv.dt[, tate4 := tate3/.N, by=c("id", "Frequency", "SampleNo", "vessel")][,tate5:=sum(tate4), by=c("id", "Frequency", "vessel")][,tate:=NULL][,tate2:=NULL][,tate3:=NULL][,tate4:=NULL]
  Sv.dt[, Perimeter:= yoko5+tate5][,yoko5:=NULL][,tate5:=NULL]
  
  #== Fractal dimension ==#
  Sv.dt[, Fractal:= 2*(log(Perimeter / 4))/log(school_area) ]
  


  #== make r(f) data table ==#

  School.dt <- Sv.dt |>
    dplyr::group_by(id, category, Frequency, Date, PingNo, pixelNo, SampleCount, DepthStart, DepthStop, sV_mean, sV_max, sV_min, sV_stdv, sV_var, rf,SE, sA, school_area, school_length, meanDepth, Perimeter, Fractal, vessel) |>
    dplyr::summarise(dplyr::across(c("Latitude", "Longitude", "YMD_time", "weighted_meanDepth", "nor_Depth", "nor_DepthStart", "nor_DepthStop", "DepthfromBottom", "BottomAltitude"), mean))


  
  School.dt <- as.data.table(School.dt)
  School.dt <- School.dt[order(vessel, id),]
  attr(School.dt$YMD_time, "tzone") <- "UTC"

  
  #== add original id  ==#
  School.dt <- as.data.table(School.dt)
  School.dt <- School.dt[order(vessel, YMD_time),]
  School.dt[, original_id := id]
  setDT(School.dt)[, id:= 1:.N, by=c("vessel", "Frequency")]
  #setDT(School.dt)[vessel == "SD1031", id:= max(School.dt[vessel=="EROS"]$id) + 1:.N, by = c("Frequency")]
  setDT(School.dt)[vessel == "SD1032", id:= max(School.dt[vessel=="SD1031"]$id) + 1:.N, by = c("Frequency")]

    
  #== sun altitude ==#
  latlon <- subset(School.dt, select=c(Latitude, Longitude, YMD_time))
  colnames(latlon) <- c("lat", "lon", "date")
  altitude.df <- suncalc::getSunlightPosition(data=latlon, keep = c("altitude"))
  School.dt <- cbind(School.dt, altitude.df)
  School.dt <- subset(School.dt, select=-c(lat,lon, date))
  School.dt$altitude_degree <- School.dt$altitude*180/pi
  
  ##== add area ==##
  test <- spdf %>% split(spdf$id) %>% 
    lapply(function(x) rbind(x,x[1,])) %>%
    lapply(function(x) x[,1:2]) %>%
    lapply(function(x) list(as.matrix(x))) %>%
    lapply(function(x) st_polygon(x))
  points <- st_as_sf(School.dt, coords=c('Longitude','Latitude'),remove = F)
  polys <- test %>% st_sfc() %>% st_sf(geom=.) %>% mutate(id=factor(1:13)) 
  temp <- polys  %>% st_intersection(points) 
  temp <- mutate (temp, area = case_when (id=="1" ~ "AlbjoernLing", id=="2" ~ "VestbankenSouthEast",
                                          id=="3" ~ "VestbankenSouthWest", id=="4" ~ "Vestbanken_North",
                                          id=="5" ~ "Vikingbanken", id=="6" ~ "Engelsk_Klondyke",
                                          id=="7" ~ "Inner_Shoal_East_2016", id=="8" ~ "Inner_Shoal_North",
                                          id=="9" ~ "Inner_Shoal_West_2018", id=="10" ~ "Inner_Shoal_test",
                                          id=="11" ~ "Nordgyden", id=="12" ~ "Ostbanken",
                                          TRUE ~ "Outer_Shoal"))
  
  temp <- data.table(vessel=temp$vessel, id=temp$id.1, area=temp$area)
  temp <- temp[!duplicated(temp[,c('id')]),] # the first area will be remain for data which are on a border of 2 areas 
  temp2 <- data.table(id=School.dt$id)
  t <- merge(x = temp2, y = temp, by = "id", all.x = TRUE)
  t[is.na(t$area)]$area = "outside"
  School.dt$area <- t$area
  
  
  #== school height, Elongation, Rectangularity =##
  setDT(School.dt)[, school_height:=DepthStop-DepthStart][, Elongation:=school_length/school_height]
  setDT(School.dt)[, school_rect:=(school_length*school_height)/school_area]
  setDT(School.dt)[, school_circ:=(Perimeter^2)/(4*pi*school_area)]
  
  
  #== add bottom depth ==#
  setDT(School.dt)[ ,bottom_Depth := weighted_meanDepth / nor_Depth]
  
  #== add coverage name ==#
  label <- unique(data.table(vessel = gps.dt$vessel, coverage_name = gps.dt$coverage_name, 
                             StartTime = gps.dt$StartTime, StopTime = gps.dt$StopTime,
                             distance_sum = gps.dt$distance_sum, 
                             area = gps.dt$area_most))
  setDT(School.dt)[setDT(label), on =. (YMD_time >= StartTime, 
                                        YMD_time <= StopTime,
                                        vessel == vessel,
                                        area == area), 
                   coverage_name := coverage_name]
  
  setDT(School.dt)[, coverage_name := ifelse(is.na(coverage_name), paste(vessel, "outside", "1", sep = "-"), coverage_name)]
  
  
  
  
  return(School.dt)
  
}


#===================================================================#



#=====================#
####   load data   ####
#=====================#

lapply(c("rawSv_data/SvSchool_SD1032_SAND_new.Rdata", "rawSv_data/SvSchool_SD1032_Predator.Rdata", "rawSv_data/SvSchool_SD1031_Predator.Rdata", "C:/Data/gps.Rdata", "C:/Data/spdf.Rdata"),load,.GlobalEnv)


rawSv.dt <- rbind(Svschool_SD1032_SAND_new, Svschool_SD1032_Predator, Svschool_SD1031_Predator)
rm(Svschool_SD1032_SAND_new, Svschool_SD1032_Predator, Svschool_SD1031_Predator)





#============================#
####   run the function   ####
#============================#

School.dt <- makeSchoolDt(rawSv.dt = rawSv.dt, spdf = spdf, gps.dt = gps.dt)
sandeel.dt <- subset(School.dt, category %in% c("SAND_new"))
predator.dt <- subset(School.dt, category %in% c("Predator"))

save(sandeel.dt, file = "sandeel.Rdata")
save(predator.dt, file = "predator.Rdata")


