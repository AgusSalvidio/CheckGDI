from application_context import ApplicationContext
from process_checker import ProcessChecker

applicationContext = ApplicationContext()
processChecker = ProcessChecker.workingWith(applicationContext)

processChecker.startChecking(applicationContext.loadedProcess())
