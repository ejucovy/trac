def functionalSuite(suite=None):
    if not suite:
        import trac.tests.functional
        suite = trac.tests.functional.functionalSuite()
    
    import trac.ticket.tests.functional.main
    trac.ticket.tests.functional.main.functionalSuite(suite)

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='functionalSuite')
