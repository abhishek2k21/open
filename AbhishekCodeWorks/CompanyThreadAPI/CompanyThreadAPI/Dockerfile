FROM openjdk:17-jdk-slim

VOLUME /tmp

COPY target/CompanyThreadAPI.jar app.jar

ENTRYPOINT ["java", "-jar", "/app.jar"]